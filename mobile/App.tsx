import { useEffect, useState } from 'react';
import { Alert, Animated, Image, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import * as Crypto from 'expo-crypto';
import { File, UploadType } from 'expo-file-system';
import { ImageManipulator, SaveFormat } from 'expo-image-manipulator';
import * as ImagePicker from 'expo-image-picker';
import * as Location from 'expo-location';
import { supabase } from './supabase';
import VoiceRecorder from './VoiceRecorder';
import WelcomeScreen from './WelcomeScreen';
import { colors, space } from './theme';
import { ActionButton, LoadingMark, useReducedMotion } from './ui';

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
  if (!supabase) throw new Error('El servicio no está disponible. Intenta más tarde.');
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
  const [severity, setSeverity] = useState<Severity | ''>('');
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
  const [welcomeDone, setWelcomeDone] = useState(false);
  const [showWelcome, setShowWelcome] = useState(true);
  const [initializing, setInitializing] = useState(true);
  const [welcomeFade] = useState(() => new Animated.Value(1));
  const [screenOpacity] = useState(() => new Animated.Value(1));
  const reducedMotion = useReducedMotion();

  useEffect(() => {
    const timer = setTimeout(() => setWelcomeDone(true), 1500);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!welcomeDone || initializing) return;
    const animation = Animated.timing(welcomeFade, { toValue: 0, duration: reducedMotion ? 0 : 180, useNativeDriver: true });
    animation.start(({ finished }) => { if (finished) setShowWelcome(false); });
    return () => animation.stop();
  }, [welcomeDone, initializing, reducedMotion, welcomeFade]);

  useEffect(() => {
    if (reducedMotion) { screenOpacity.setValue(1); return; }
    screenOpacity.setValue(0);
    const animation = Animated.timing(screenOpacity, { toValue: 1, duration: 180, useNativeDriver: true });
    animation.start();
    return () => animation.stop();
  }, [screen, reducedMotion, screenOpacity]);

  const loadCategories = async () => {
    setBusy(true); setMessage('');
    try {
      if (!apiUrl) throw new Error('El servicio no está disponible. Intenta más tarde.');
      const token = await getToken();
      const response = await fetch(`${apiUrl}/categories`, { headers: { Authorization: `Bearer ${token}` } });
      if (!response.ok) throw new Error('No se pudieron cargar las categorías. Intenta de nuevo.');
      setCategories((await response.json()).items);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'No se pudo conectar');
    } finally { setBusy(false); setInitializing(false); }
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
    if (!apiUrl) throw new Error('El servicio no está disponible. Intenta más tarde.');
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
      throw new Error(data.error?.message || 'No se pudo transcribir. Intenta de nuevo.');
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
        ? 'Revisa los campos sugeridos antes de enviar.'
        : 'Solo se llenó la descripción. Elige y revisa los demás campos antes de enviar.');
    return true;
  };

  const review = () => {
    if (voiceRecording) return setMessage('Detén la grabación antes de revisar el formulario');
    if (!categories.some((item) => item.id === categoryId) || !description.trim() || !severity || !coordinates) {
      Alert.alert('Favor de llenar todos los campos antes de REVISAR REPORTE');
      return;
    }
    if (description.trim().length < 10) return Alert.alert('Describe el problema con al menos 10 caracteres');
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
    if (!apiUrl) throw new Error('El servicio no está disponible. Intenta más tarde.');
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
        let detail = 'No se pudo subir la foto';
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
      if (!response.ok) throw new Error(data.error?.message || 'No se pudo enviar. Intenta de nuevo.');
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
    setCategoryId(''); setDescription(''); setDuration(''); setSeverity('');
    setCoordinates(null); setRequestId(''); setIncidentId(''); setReportId(''); setPhotos([]); setUploadedPhotos(0);
    setMessage(''); setNotice(''); setInputMethod('traditional'); setSuggestedFields([]); setNearby([]); setScreen('form');
  };
  const selectedCategory = categories.find((item) => item.id === categoryId);
  const photoPreviews = photos.map((uri, index) => <View key={uri} style={styles.photoItem}>
    <Image source={{ uri }} style={styles.photoImage} accessibilityLabel={`Foto ${index + 1} del reporte`} />
    {screen === 'form' ? <ActionButton title="Quitar foto" variant="danger" onPress={() => removePhoto(uri)} disabled={busy} /> : null}
  </View>);

  if (showWelcome) return <Animated.View style={{ flex: 1, opacity: welcomeFade }}><WelcomeScreen ready={!initializing} /></Animated.View>;

  return (
    <View style={styles.root}>
    <ScrollView style={styles.page} contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
      <View style={styles.brandRow}><Image source={require('./assets/pulso-icon.png')} style={styles.brandImage} accessible={false} />
        <Text style={styles.brandName}>PULSO URBANO</Text></View>
      <Text style={styles.title}>{screen === 'form' ? 'Nuevo reporte' : screen === 'review' ? 'Revisa tu reporte' : screen === 'sent' ? 'Reporte recibido' : 'Cerca de ti'}</Text>
      {message ? <Text style={styles.error} accessibilityRole="alert">{message}</Text> : null}
      {notice ? <Text style={styles.notice} accessibilityRole="alert">{notice}</Text> : null}
      <Animated.View style={{ opacity: screenOpacity, transform: [{ translateY: screenOpacity.interpolate({ inputRange: [0, 1], outputRange: [8, 0] }) }] }}>
      {screen === 'form' && <>
        <View style={styles.progress}><Text style={styles.progressText}>PASO 1 DE 2</Text><Text style={styles.progressDetail}>Cuéntanos qué sucede</Text></View>
        <View style={styles.section}>
          <Text style={styles.sectionNumber}>01  ·  PROBLEMA</Text>
          <Text style={styles.sectionTitle}>¿Qué problema encontraste?</Text>
          <VoiceRecorder onRecordingChange={setVoiceRecording} onAudioReady={processVoice} />
          <Text style={styles.label}>O selecciona una categoría</Text>
          {categories.length === 0 && !busy ? <ActionButton title="Reintentar carga de categorías" variant="secondary" onPress={loadCategories} /> : null}
          <View style={styles.options}>{categories.map((item) =>
            <Pressable key={item.id} accessibilityRole="radio" accessibilityState={{ selected: categoryId === item.id }}
              onPress={() => setCategoryId(item.id)} style={[styles.option, categoryId === item.id && styles.selected]}>
              <Text style={[styles.optionText, categoryId === item.id && styles.selectedText]}>{item.name}</Text>
            </Pressable>)}</View>
        </View>
        <View style={styles.section}>
          <Text style={styles.sectionNumber}>02  ·  DESCRIPCIÓN</Text>
          <Text style={styles.sectionTitle}>Describe lo que sucede</Text>
          <Text style={styles.label}>Descripción</Text>
          <TextInput style={[styles.input, styles.multiline]} multiline value={description} onChangeText={setDescription}
            accessibilityLabel="Descripción del problema" placeholder="Escribe aquí, sin datos personales" placeholderTextColor={colors.muted} maxLength={1000} />
          {suggestedFields.length > 0 ? <Text style={styles.suggestion}>Revisa los datos sugeridos; puedes cambiarlos.</Text> : null}
          <Text style={styles.label}>¿Desde cuándo? <Text style={styles.optional}>(opcional)</Text></Text>
          <TextInput style={styles.input} value={duration} onChangeText={setDuration} accessibilityLabel="Desde cuándo ocurre"
            placeholder="Ej. desde hace tres días" placeholderTextColor={colors.muted} maxLength={100} />
          <Text style={styles.label}>Gravedad observada</Text>
          <View style={styles.options}>{severities.map((item) =>
            <Pressable key={item.value} accessibilityRole="radio" accessibilityState={{ selected: severity === item.value }}
              onPress={() => setSeverity(item.value)} style={[styles.option, severity === item.value && styles.selected]}>
              <Text style={[styles.optionText, severity === item.value && styles.selectedText]}>{item.label}</Text>
            </Pressable>)}</View>
        </View>
        <View style={styles.section}>
          <Text style={styles.sectionNumber}>03  ·  EVIDENCIA</Text>
          <Text style={styles.sectionTitle}>Agrega fotografías <Text style={styles.optional}>(opcional)</Text></Text>
          <Text style={styles.note}>Máximo 2. Evita personas, placas y datos personales.</Text>
          <ActionButton title="Elegir de galería" variant="secondary" onPress={() => { void addPhoto('library'); }} disabled={busy || photos.length >= 2} />
          <View style={styles.smallGap} />
          <ActionButton title="Tomar foto" variant="secondary" onPress={() => { void addPhoto('camera'); }} disabled={busy || photos.length >= 2} />
          {photos.length > 0 ? <View style={styles.photoList}>{photoPreviews}</View> : null}
        </View>
        <View style={styles.section}>
          <Text style={styles.sectionNumber}>04  ·  UBICACIÓN</Text>
          <Text style={styles.sectionTitle}>Confirma dónde ocurre</Text>
          <ActionButton title={coordinates ? 'Actualizar ubicación' : 'Obtener mi ubicación'} variant="secondary" onPress={useGps} disabled={busy} />
          {coordinates ? <Text style={styles.verified}>✓ Ubicación obtenida</Text> : null}
        </View>
        <ActionButton title="Revisar reporte" onPress={review} disabled={busy || voiceRecording || categories.length === 0} />
        <View style={styles.nearbyLink}><Text style={styles.nearbyText}>¿Ya se reportó este problema?</Text>
          <ActionButton title="Ver incidentes cercanos" variant="secondary" onPress={() => { void openNearby(); }} disabled={busy} /></View>
      </>}
      {screen === 'review' && <>
        <View style={styles.progress}><Text style={styles.progressText}>PASO 2 DE 2</Text><Text style={styles.progressDetail}>Confirma que todo esté correcto</Text></View>
        <View style={styles.section}>
          <Text style={styles.summaryLabel}>PROBLEMA</Text><Text style={styles.summaryValue}>{selectedCategory?.name}</Text>
          <Text style={styles.summaryLabel}>DESCRIPCIÓN</Text><Text style={styles.summaryValue}>{description.trim()}</Text>
          <Text style={styles.summaryLabel}>DESDE CUÁNDO</Text><Text style={styles.summaryValue}>{duration.trim() || 'No indicado'}</Text>
          <Text style={styles.summaryLabel}>GRAVEDAD</Text><Text style={styles.summaryValue}>{severities.find((item) => item.value === severity)?.label}</Text>
          <Text style={styles.summaryLabel}>UBICACIÓN</Text><Text style={styles.verified}>✓ Confirmada por GPS</Text>
          <Text style={styles.summaryLabel}>FOTOGRAFÍAS</Text><Text style={styles.summaryValue}>{photos.length}</Text>
          {photos.length > 0 ? <View style={styles.photoList}>{photoPreviews}</View> : null}
        </View>
        <ActionButton title="Confirmar y enviar" onPress={send} disabled={busy} busy={busy} />
        <View style={styles.smallGap} />
        <ActionButton title="Editar datos" variant="secondary" onPress={() => { setRequestId(''); setMessage(''); setScreen('form'); }} disabled={busy} />
      </>}
      {screen === 'sent' && <>
        <View style={[styles.section, styles.sentCard]}>
          <Text style={styles.sentIcon}>✓</Text>
          <Text style={styles.sectionTitle}>Tu reporte quedó registrado</Text>
          <Text style={styles.note}>Folio: {incidentId}</Text>
          {uploadedPhotos + photos.length > 0 ? <Text style={styles.note}>Fotografías guardadas: {uploadedPhotos}{photos.length > 0 ? ` · Pendientes: ${photos.length}` : ''}</Text> : null}
        </View>
        {photos.length > 0 ? <>
          <View style={styles.photoList}>{photoPreviews}</View>
          <ActionButton title="Reintentar fotos pendientes" variant="secondary" onPress={() => { void retryPhotos(); }} disabled={busy} />
          <Text style={styles.note}>Si creas otro reporte, las fotos pendientes no se enviarán.</Text>
        </> : null}
        <ActionButton title="Crear otro reporte" onPress={reset} disabled={busy} />
      </>}
      {screen === 'nearby' && <>
        <Text style={styles.note}>Confirma solo si el problema sigue ocurriendo.</Text>
        {nearby.length === 0 ? <View style={styles.section}><Text style={styles.summaryValue}>No hay incidentes de otras personas cerca de ti.</Text></View> : null}
        {nearby.map((item) => <View key={item.id} style={styles.nearbyItem}>
          <Text style={styles.nearbyTitle}>{item.category_name}</Text>
          <Text style={styles.note}>A unos {item.distance_m_approx} m · reportado el {item.reported_on}</Text>
          <Text style={styles.summaryValue}>Confirmaciones: {item.confirmations_count}</Text>
          <ActionButton title={item.confirmed_by_me ? 'Ya confirmaste este incidente' : 'Confirmar que sigue ocurriendo'}
            onPress={() => { void confirmNearby(item.id); }} disabled={busy || item.confirmed_by_me} />
        </View>)}
        <ActionButton title="Volver al formulario" variant="secondary" onPress={() => { setMessage(''); setNotice(''); setScreen('form'); }} disabled={busy} />
      </>}
      </Animated.View>
    </ScrollView>
    {busy ? <View style={styles.busyToast} pointerEvents="none"><LoadingMark label={screen === 'sent' ? 'Guardando fotografías…' : screen === 'nearby' ? 'Consultando incidentes…' : 'Procesando…'} /></View> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.canvas },
  page: { flex: 1, backgroundColor: colors.canvas },
  busyToast: { position: 'absolute', bottom: 18, left: 18, right: 18, maxWidth: 360, alignSelf: 'center',
    backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.line, borderRadius: 18, elevation: 7,
    shadowColor: colors.ink, shadowOpacity: 0.14, shadowRadius: 16, shadowOffset: { width: 0, height: 6 } },
  container: { width: '100%', maxWidth: 640, alignSelf: 'center', paddingHorizontal: 18, paddingTop: 58, paddingBottom: 72, flexGrow: 1 },
  brandRow: { flexDirection: 'row', alignItems: 'center', gap: space.sm, marginBottom: space.md },
  brandImage: { width: 40, height: 40, borderRadius: 12 },
  brandName: { color: colors.primaryDark, fontSize: 13, fontWeight: '800', letterSpacing: 1.3 },
  title: { fontSize: 32, lineHeight: 38, fontWeight: '800', color: colors.ink, marginBottom: space.lg },
  progress: { backgroundColor: colors.softBlue, borderRadius: 16, padding: space.md, marginBottom: space.md,
    borderLeftWidth: 4, borderLeftColor: colors.cyan },
  progressText: { color: colors.primary, fontSize: 12, fontWeight: '800', letterSpacing: 1.1, marginBottom: space.xs },
  progressDetail: { color: colors.ink, fontSize: 16, fontWeight: '600' },
  section: { backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.line, borderRadius: 18,
    padding: space.md, marginBottom: space.md },
  sectionNumber: { color: colors.violet, fontSize: 12, fontWeight: '800', letterSpacing: 1, marginBottom: space.sm },
  sectionTitle: { color: colors.ink, fontSize: 21, lineHeight: 28, fontWeight: '800', marginBottom: space.md },
  label: { color: colors.ink, fontSize: 16, fontWeight: '700', marginTop: space.md, marginBottom: space.sm },
  optional: { color: colors.muted, fontSize: 15, fontWeight: '400' },
  note: { color: colors.muted, fontSize: 15, lineHeight: 22, marginBottom: space.md },
  error: { color: colors.danger, backgroundColor: colors.dangerBg, borderRadius: 12, padding: space.md, marginBottom: space.md, fontSize: 16 },
  notice: { color: colors.success, backgroundColor: colors.successBg, borderRadius: 12, padding: space.md, marginBottom: space.md, fontSize: 16 },
  input: { minHeight: 54, borderColor: colors.line, borderWidth: 1.5, borderRadius: 12, padding: 14,
    fontSize: 16, color: colors.ink, backgroundColor: colors.surface },
  multiline: { minHeight: 130, textAlignVertical: 'top' },
  options: { flexDirection: 'row', flexWrap: 'wrap', gap: space.sm },
  option: { flexGrow: 1, flexBasis: '44%', minWidth: 112, minHeight: 54, borderWidth: 1.5,
    borderColor: colors.line, borderRadius: 12, padding: 12, alignItems: 'center', justifyContent: 'center' },
  selected: { borderColor: colors.primary, backgroundColor: colors.softBlue },
  optionText: { color: colors.ink, fontSize: 15, fontWeight: '600', textAlign: 'center' },
  selectedText: { color: colors.primaryDark, fontWeight: '800' },
  verified: { color: colors.success, fontSize: 16, fontWeight: '700', marginTop: space.md },
  suggestion: { color: colors.warning, backgroundColor: colors.warningBg, padding: space.md,
    borderRadius: 12, marginTop: space.sm },
  summaryLabel: { color: colors.muted, fontSize: 12, fontWeight: '800', letterSpacing: 1,
    marginTop: space.md, marginBottom: space.xs },
  summaryValue: { color: colors.ink, fontSize: 17, lineHeight: 24 },
  smallGap: { height: space.sm },
  photoList: { flexDirection: 'row', flexWrap: 'wrap', gap: space.md, marginVertical: space.md },
  photoItem: { gap: space.sm },
  photoImage: { width: 120, height: 120, borderRadius: 12 },
  nearbyLink: { marginTop: space.xl, gap: space.sm },
  nearbyText: { textAlign: 'center', color: colors.muted, fontSize: 16 },
  nearbyItem: { backgroundColor: colors.surface, borderColor: colors.line, borderWidth: 1,
    borderRadius: 18, padding: space.md, marginBottom: space.md, gap: space.sm },
  nearbyTitle: { fontSize: 20, fontWeight: '800', color: colors.ink },
  sentCard: { alignItems: 'center', paddingVertical: space.xl },
  sentIcon: { width: 56, height: 56, borderRadius: 28, backgroundColor: colors.successBg,
    color: colors.success, textAlign: 'center', textAlignVertical: 'center', fontSize: 30,
    fontWeight: '800', overflow: 'hidden', marginBottom: space.md },
});
