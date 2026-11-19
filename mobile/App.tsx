import { useEffect, useState } from 'react';
import { ActivityIndicator, Button, Image, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import * as Crypto from 'expo-crypto';
import { File, UploadType } from 'expo-file-system';
import { ImageManipulator, SaveFormat } from 'expo-image-manipulator';
import * as ImagePicker from 'expo-image-picker';
import * as Location from 'expo-location';
import { supabase } from './supabase';
import VoiceRecorder from './VoiceRecorder';

type Category = { id: string; code: string; name: string; default_severity: string };
type Severity = 'low' | 'medium' | 'high' | 'critical';
type Coordinates = { latitude: number; longitude: number };
type Screen = 'form' | 'review' | 'sent' | 'nearby';
type NearbyIncident = {
  id: string; category_name: string; distance_m_approx: number; reported_on: string;
  confirmations_count: number; confirmed_by_me: boolean;
};
type VoiceResponse = {
  mode: 'suggested' | 'manual_fallback';
  transcription: string | null;
  draft: {
    description: string | null;
    category_id: string | null;
    duration_text: string | null;
    severity_proposed: Severity | null;
  };
  reason?: string;
  error?: { message: string };
};

const apiUrl = process.env.EXPO_PUBLIC_API_URL;
const severities: { value: Severity; label: string }[] = [
  { value: 'low', label: 'Baja' }, { value: 'medium', label: 'Media' },
  { value: 'high', label: 'Alta' }, { value: 'critical', label: 'Crítica' },
];

async function getToken(): Promise<string> {
  if (!supabase) throw new Error('Configura la URL y la clave publicable de Supabase en mobile/.env');
  const { data, error } = await supabase.auth.getSession();
  if (error) throw new Error('No se pudo recuperar la sesión');
  if (data.session) {
    if (!data.session.user.is_anonymous) throw new Error('Esta app requiere una sesión ciudadana anónima');
    return data.session.access_token;
  }
  const created = await supabase.auth.signInAnonymously();
  if (created.error || !created.data.session) throw new Error('No se pudo iniciar la sesión anónima');
  return created.data.session.access_token;
}

export default function App() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [categoryId, setCategoryId] = useState('');
  const [description, setDescription] = useState('');
  const [duration, setDuration] = useState('');
  const [severity, setSeverity] = useState<Severity>('medium');
  const [coordinates, setCoordinates] = useState<Coordinates | null>(null);
  const [screen, setScreen] = useState<Screen>('form');
  const [requestId, setRequestId] = useState('');
  const [incidentId, setIncidentId] = useState('');
  const [reportId, setReportId] = useState('');
  const [photos, setPhotos] = useState<string[]>([]);
  const [uploadedPhotos, setUploadedPhotos] = useState(0);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [notice, setNotice] = useState('');
  const [voiceRecording, setVoiceRecording] = useState(false);
  const [inputMethod, setInputMethod] = useState<'traditional' | 'voice'>('traditional');
  const [suggestedFields, setSuggestedFields] = useState<string[]>([]);
  const [nearby, setNearby] = useState<NearbyIncident[]>([]);

  const loadCategories = async () => {
    setBusy(true); setMessage('');
    try {
      if (!apiUrl) throw new Error('Configura EXPO_PUBLIC_API_URL en mobile/.env');
      const token = await getToken();
      const response = await fetch(`${apiUrl}/categories`, { headers: { Authorization: `Bearer ${token}` } });
      if (!response.ok) throw new Error(`No se pudieron cargar las categorías (HTTP ${response.status})`);
      setCategories((await response.json()).items);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'No se pudo conectar');
    } finally { setBusy(false); }
  };

  useEffect(() => {
    const timer = setTimeout(() => { void loadCategories(); }, 0);
    return () => clearTimeout(timer);
  }, []);

  const getGpsPoint = async (): Promise<Coordinates> => {
    const permission = await Location.requestForegroundPermissionsAsync();
    if (permission.status !== 'granted') throw new Error('Activa el permiso de ubicación para continuar');
    const position = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
    return { latitude: position.coords.latitude, longitude: position.coords.longitude };
  };

  const useGps = async () => {
    setBusy(true); setMessage('');
    try { setCoordinates(await getGpsPoint()); }
    catch (error) { setMessage(error instanceof Error ? error.message : 'No se pudo obtener la ubicación'); }
    finally { setBusy(false); }
  };

  const openNearby = async () => {
    if (busy || !apiUrl) return;
    setBusy(true); setMessage(''); setNotice('');
    try {
      const point = await getGpsPoint();
      const token = await getToken();
      const params = new URLSearchParams({ latitude: String(point.latitude), longitude: String(point.longitude) });
      const response = await fetch(`${apiUrl}/incidents/nearby?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error?.message || 'No se pudieron buscar incidentes cercanos');
      setNearby(data.items); setScreen('nearby');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'No se pudo consultar la zona');
    } finally { setBusy(false); }
  };

  const confirmNearby = async (id: string) => {
    if (busy || !apiUrl) return;
    setBusy(true); setMessage(''); setNotice('');
    try {
      const point = await getGpsPoint();
      const token = await getToken();
      const response = await fetch(`${apiUrl}/incidents/${id}/confirmations`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(point),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error?.message || 'No se pudo confirmar el incidente');
      setNearby((items) => items.map((item) => item.id === id
        ? { ...item, confirmed_by_me: true, confirmations_count: data.confirmations_count } : item));
      setNotice('Confirmación guardada. Gracias por verificar el problema.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'No se pudo confirmar');
    } finally { setBusy(false); }
  };

  const processVoice = async (uri: string): Promise<boolean> => {
    if (!apiUrl) throw new Error('Configura EXPO_PUBLIC_API_URL en mobile/.env');
    const token = await getToken();
    const file = new File(uri);
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 60000);
    let response: { status: number; body: string };
    try {
      response = await file.upload(`${apiUrl}/ai/process-voice-report`, {
        httpMethod: 'POST', uploadType: UploadType.MULTIPART, fieldName: 'audio', mimeType: 'audio/mp4',
        headers: { Authorization: `Bearer ${token}` }, signal: controller.signal,
      });
    } catch (error) {
      throw new Error(controller.signal.aborted
        ? 'La transcripción tardó demasiado. Intenta otra vez o escribe el reporte.'
        : `No se pudo subir el audio: ${error instanceof Error ? error.message : 'error desconocido'}`);
    } finally { clearTimeout(timeout); }
    const data: VoiceResponse = JSON.parse(response.body);
    if (response.status < 200 || response.status >= 300) {
      throw new Error(data.error?.message || `No se pudo transcribir (HTTP ${response.status})`);
    }
    const text = data.draft?.description || data.transcription;
    if (!text) {
      setMessage('No se reconoció texto. Puedes escribir la descripción manualmente.');
      return false;
    }
    if (text.length > 1000) {
      setMessage('La transcripción es demasiado larga. Resume el problema manualmente.');
      return false;
    }
    setDescription(text);
    setInputMethod('voice');
    const applied: string[] = [];
    if (data.mode === 'suggested') {
      const category = data.draft.category_id;
      if (category && (categories.length === 0 || categories.some((item) => item.id === category))) {
        setCategoryId(category);
        applied.push('categoría');
      }
      const proposedDuration = data.draft.duration_text;
      if (proposedDuration && proposedDuration.length <= 100) {
        setDuration(proposedDuration);
        applied.push('desde cuándo');
      }
      const proposedSeverity = data.draft.severity_proposed;
      if (proposedSeverity && severities.some((item) => item.value === proposedSeverity)) {
        setSeverity(proposedSeverity);
        applied.push('gravedad');
      }
    }
    setSuggestedFields(applied);
    setMessage(data.reason === 'REDACTION_REVIEW_REQUIRED'
      ? 'Se omitieron posibles datos personales. Revisa y corrige la descripción antes de enviar.'
      : applied.length > 0
        ? `La IA llenó ${applied.join(', ')} como propuesta. Revisa y corrige todos los campos antes de enviar.`
        : 'Solo se llenó la descripción. Elige y revisa los demás campos antes de enviar.');
    return true;
  };

  const review = () => {
    if (voiceRecording) return setMessage('Detén la grabación antes de revisar el formulario');
    if (!categoryId) return setMessage('Selecciona una categoría');
    if (description.trim().length < 10) return setMessage('Describe el problema con al menos 10 caracteres');
    if (!coordinates) return setMessage('Obtén la ubicación antes de continuar');
    setRequestId(Crypto.randomUUID()); setMessage(''); setScreen('review');
  };

  const addPhoto = async (source: 'camera' | 'library') => {
    if (busy || photos.length >= 2) return;
    setBusy(true); setMessage('');
    try {
      if (source === 'camera') {
        const permission = await ImagePicker.requestCameraPermissionsAsync();
        if (!permission.granted) throw new Error('Permite usar la cámara para tomar una foto');
      }
      const result = source === 'camera'
        ? await ImagePicker.launchCameraAsync({ mediaTypes: ['images'], quality: 0.8, exif: false })
        : await ImagePicker.launchImageLibraryAsync({ mediaTypes: ['images'], quality: 0.8, exif: false });
      if (result.canceled || !result.assets[0]) return;
      const context = ImageManipulator.manipulate(result.assets[0].uri, { maxWidth: 1600, maxHeight: 1600 });
      const image = await context.renderAsync();
      const saved = await image.saveAsync({ format: SaveFormat.JPEG, compress: 0.8 });
      const file = new File(saved.uri);
      if (!file.exists || file.size === 0 || file.size > 5 * 1024 * 1024) {
        if (file.exists) file.delete();
        throw new Error('La foto no se pudo preparar o supera 5 MB');
      }
      setPhotos((current) => [...current, saved.uri]);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'No se pudo preparar la fotografía');
    } finally { setBusy(false); }
  };

  const removePhoto = (uri: string) => {
    setPhotos((current) => current.filter((item) => item !== uri));
    const file = new File(uri);
    try { if (file.exists) file.delete(); } catch { /* El caché local se puede limpiar al cerrar la app. */ }
  };

  const uploadPhotos = async (savedReportId: string, pending: string[]) => {
    if (!apiUrl) throw new Error('Configura EXPO_PUBLIC_API_URL en mobile/.env');
    const token = await getToken();
    for (const uri of pending) {
      const file = new File(uri);
      if (!file.exists) throw new Error('La fotografía temporal ya no está disponible');
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 60000);
      let response: { status: number; body: string };
      try {
        response = await file.upload(`${apiUrl}/reports/${savedReportId}/photos`, {
          httpMethod: 'POST', uploadType: UploadType.MULTIPART, fieldName: 'photo', mimeType: 'image/jpeg',
          headers: { Authorization: `Bearer ${token}` }, signal: controller.signal,
        });
      } catch (error) {
        throw new Error(controller.signal.aborted ? 'La subida de la foto tardó demasiado'
          : `No se pudo subir la foto: ${error instanceof Error ? error.message : 'error desconocido'}`);
      } finally { clearTimeout(timeout); }
      if (response.status < 200 || response.status >= 300) {
        let detail = `HTTP ${response.status}`;
        try { detail = JSON.parse(response.body).error?.message || detail; } catch { /* Respuesta sin JSON. */ }
        throw new Error(detail);
      }
      setPhotos((current) => current.filter((item) => item !== uri));
      setUploadedPhotos((count) => count + 1);
      try { file.delete(); } catch { /* La foto ya se guardó; no se debe reintentar la subida. */ }
    }
  };

  const send = async () => {
    if (busy || !coordinates || !apiUrl) return;
    setBusy(true); setMessage('');
    try {
      const token = await getToken();
      const response = await fetch(`${apiUrl}/reports`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ client_request_id: requestId, category_id: categoryId,
          description: description.trim(), duration_text: duration.trim() || null, severity,
          location: coordinates, location_source: 'gps', input_method: inputMethod }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error?.message || `No se pudo enviar (HTTP ${response.status})`);
      setReportId(data.id); setIncidentId(data.incident_id); setScreen('sent');
      if (photos.length > 0) {
        try {
          await uploadPhotos(data.id, photos);
        } catch (error) {
          setMessage(`Reporte guardado. Hay fotos pendientes: ${error instanceof Error ? error.message : 'error desconocido'}`);
        }
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'No se pudo enviar. Intenta otra vez');
    } finally { setBusy(false); }
  };

  const retryPhotos = async () => {
    if (busy || !reportId || photos.length === 0) return;
    setBusy(true); setMessage('');
    try { await uploadPhotos(reportId, photos); }
    catch (error) { setMessage(`Reporte guardado. Hay fotos pendientes: ${error instanceof Error ? error.message : 'error desconocido'}`); }
    finally { setBusy(false); }
  };

  const reset = () => {
    for (const uri of photos) {
      const file = new File(uri);
      try { if (file.exists) file.delete(); } catch { /* El caché local se puede limpiar al cerrar la app. */ }
    }
    setCategoryId(''); setDescription(''); setDuration(''); setSeverity('medium');
    setCoordinates(null); setRequestId(''); setIncidentId(''); setReportId(''); setPhotos([]); setUploadedPhotos(0);
    setMessage(''); setNotice(''); setInputMethod('traditional'); setSuggestedFields([]); setNearby([]); setScreen('form');
  };
  const selectedCategory = categories.find((item) => item.id === categoryId);
  const photoPreviews = photos.map((uri, index) => <View key={uri} style={styles.photoItem}>
    <Image source={{ uri }} style={styles.photoImage} accessibilityLabel={`Foto ${index + 1} del reporte`} />
    {screen === 'form' ? <Button title="Quitar" onPress={() => removePhoto(uri)} disabled={busy} /> : null}
  </View>);

  return (
    <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
      <Text style={styles.title}>Reporte urbano</Text>
      <Text style={styles.note}>Demo con reportes ficticios. No escribas nombres, teléfonos, correos ni domicilios personales.</Text>
      {message ? <Text style={styles.error}>{message}</Text> : null}
      {notice ? <Text style={styles.notice}>{notice}</Text> : null}
      {busy ? <ActivityIndicator style={styles.loading} /> : null}
      {screen === 'form' && <>
        <Button title="Ver incidentes cercanos" onPress={() => { void openNearby(); }} disabled={busy} />
        <Text style={styles.note}>Si el problema ya está reportado, puedes confirmarlo sin crear otro reporte.</Text>
        <VoiceRecorder onRecordingChange={setVoiceRecording} onAudioReady={processVoice} />
        {suggestedFields.length > 0 ? <Text style={styles.suggestion}>La IA llenó inicialmente: {suggestedFields.join(', ')}. Puedes cambiar cualquiera de estos datos.</Text> : null}
        <Text style={styles.label}>¿Qué problema encontraste?</Text>
        {categories.length === 0 && !busy ? <Button title="Reintentar carga de categorías" onPress={loadCategories} /> : null}
        <View style={styles.options}>{categories.map((item) =>
          <Pressable key={item.id} onPress={() => setCategoryId(item.id)} style={[styles.option, categoryId === item.id && styles.selected]}>
            <Text style={styles.optionText}>{item.name}</Text>
          </Pressable>)}</View>
        <Text style={styles.label}>Descripción</Text>
        <TextInput style={[styles.input, styles.multiline]} multiline value={description} onChangeText={setDescription} placeholder="Describe el problema sin datos personales" maxLength={1000} />
        <Text style={styles.label}>¿Desde cuándo? (opcional)</Text>
        <TextInput style={styles.input} value={duration} onChangeText={setDuration} placeholder="Ej. tres días" maxLength={100} />
        <Text style={styles.label}>Gravedad observada</Text>
        <View style={styles.options}>{severities.map((item) =>
          <Pressable key={item.value} onPress={() => setSeverity(item.value)} style={[styles.option, severity === item.value && styles.selected]}>
            <Text style={styles.optionText}>{item.label}</Text>
          </Pressable>)}</View>
        <Text style={styles.label}>Ubicación GPS</Text>
        <Button title={coordinates ? 'Actualizar ubicación' : 'Obtener ubicación'} onPress={useGps} disabled={busy} />
        <Text style={styles.note}>{coordinates ? `${coordinates.latitude.toFixed(5)}, ${coordinates.longitude.toFixed(5)}` : 'Aún no se ha obtenido la ubicación'}</Text>
        <Text style={styles.label}>Fotografías (opcional, máximo 2)</Text>
        <Text style={styles.note}>Usa solo imágenes ficticias. Revisa que no aparezcan personas, placas ni datos personales.</Text>
        <Button title="Elegir de galería" onPress={() => { void addPhoto('library'); }} disabled={busy || photos.length >= 2} />
        <View style={styles.smallGap} />
        <Button title="Tomar foto" onPress={() => { void addPhoto('camera'); }} disabled={busy || photos.length >= 2} />
        <View style={styles.photoList}>{photoPreviews}</View>
        <Button title="Revisar reporte" onPress={review} disabled={busy || voiceRecording || categories.length === 0} />
      </>}
      {screen === 'review' && <>
        <Text style={styles.subtitle}>Revisa antes de confirmar</Text>
        <Text style={styles.summary}>Categoría: {selectedCategory?.name}</Text>
        <Text style={styles.summary}>Descripción: {description.trim()}</Text>
        <Text style={styles.summary}>Desde cuándo: {duration.trim() || 'No indicado'}</Text>
        <Text style={styles.summary}>Gravedad: {severities.find((item) => item.value === severity)?.label}</Text>
        <Text style={styles.summary}>Origen: {inputMethod === 'voice' ? 'voz (texto corregible)' : 'formulario'}</Text>
        {suggestedFields.length > 0 ? <Text style={styles.note}>La IA sugirió inicialmente {suggestedFields.join(', ')}. Confirma que los valores mostrados sean correctos.</Text> : null}
        <Text style={styles.summary}>GPS: {coordinates?.latitude.toFixed(5)}, {coordinates?.longitude.toFixed(5)}</Text>
        <Text style={styles.summary}>Fotografías: {photos.length}</Text>
        <View style={styles.photoList}>{photoPreviews}</View>
        <Text style={styles.note}>Si algo está mal, vuelve y corrígelo. El reporte se guarda solo al confirmar.</Text>
        <Button title="Editar datos" onPress={() => { setRequestId(''); setMessage(''); setScreen('form'); }} disabled={busy} />
        <View style={styles.gap} /><Button title="Confirmar y enviar" onPress={send} disabled={busy} />
      </>}
      {screen === 'sent' && <>
        <Text style={styles.subtitle}>Reporte enviado</Text>
        <Text style={styles.summary}>Tu incidente se registró con estado “reportado”.</Text>
        <Text style={styles.note}>ID del incidente: {incidentId}</Text>
        <Text style={styles.summary}>Fotografías guardadas: {uploadedPhotos}{photos.length > 0 ? `; pendientes: ${photos.length}` : ''}</Text>
        {busy && photos.length > 0 ? <Text style={styles.note}>Subiendo fotografías...</Text> : null}
        {photos.length > 0 ? <>
          <View style={styles.photoList}>{photoPreviews}</View>
          <Button title="Reintentar fotos pendientes" onPress={() => { void retryPhotos(); }} disabled={busy} />
          <Text style={styles.note}>Si creas otro reporte, las fotos pendientes no se enviarán.</Text>
        </> : null}
        <Button title="Crear otro reporte" onPress={reset} disabled={busy} />
      </>}
      {screen === 'nearby' && <>
        <Text style={styles.subtitle}>Incidentes cercanos</Text>
        <Text style={styles.note}>Se muestran problemas activos hasta 1 km de ti, sin dirección exacta. Confirma solo si ves que el problema sigue ocurriendo. Tus propios reportes no aparecen aquí.</Text>
        {nearby.length === 0 ? <Text style={styles.summary}>No hay incidentes de otras sesiones cerca de ti.</Text> : null}
        {nearby.map((item) => <View key={item.id} style={styles.nearbyItem}>
          <Text style={styles.nearbyTitle}>{item.category_name}</Text>
          <Text style={styles.note}>A unos {item.distance_m_approx} m · reportado el {item.reported_on}</Text>
          <Text style={styles.summary}>Confirmaciones de otras sesiones: {item.confirmations_count}</Text>
          <Button title={item.confirmed_by_me ? 'Ya confirmaste este incidente' : 'Confirmar que sigue ocurriendo'}
            onPress={() => { void confirmNearby(item.id); }} disabled={busy || item.confirmed_by_me} />
        </View>)}
        <Button title="Volver al formulario" onPress={() => { setMessage(''); setNotice(''); setScreen('form'); }} disabled={busy} />
      </>}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 24, paddingTop: 60, paddingBottom: 60, backgroundColor: '#fff', flexGrow: 1 },
  title: { fontSize: 28, fontWeight: '700', color: '#14324a', marginBottom: 10 },
  subtitle: { fontSize: 22, fontWeight: '700', color: '#14324a', marginBottom: 16 },
  label: { fontSize: 16, fontWeight: '600', marginTop: 18, marginBottom: 8 },
  note: { color: '#53636f', lineHeight: 20, marginBottom: 18, marginTop: 8 },
  error: { color: '#a52828', marginVertical: 12 },
  notice: { color: '#27633d', marginVertical: 12 },
  input: { borderColor: '#aebbc5', borderWidth: 1, borderRadius: 8, padding: 12, fontSize: 16 },
  multiline: { minHeight: 110, textAlignVertical: 'top' },
  options: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  option: { borderWidth: 1, borderColor: '#aebbc5', borderRadius: 8, padding: 10 },
  selected: { borderColor: '#0866a3', backgroundColor: '#d9efff' },
  optionText: { color: '#14324a' },
  summary: { fontSize: 16, lineHeight: 23, marginBottom: 14 },
  suggestion: { color: '#7a4d00', backgroundColor: '#fff4d6', padding: 12, borderRadius: 8, marginBottom: 8 },
  loading: { marginVertical: 12 }, gap: { height: 16 },
  smallGap: { height: 8 },
  photoList: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, marginVertical: 12 },
  photoItem: { gap: 6 },
  photoImage: { width: 120, height: 120, borderRadius: 8 },
  nearbyItem: { borderColor: '#d7e0e6', borderWidth: 1, borderRadius: 8, padding: 16, marginBottom: 14 },
  nearbyTitle: { fontSize: 18, fontWeight: '700', color: '#14324a' },
});
