import { useRef, useState } from 'react';
import { Button, StyleSheet, Text, View } from 'react-native';
import { AudioModule, RecordingPresets, setAudioModeAsync, useAudioRecorder, useAudioRecorderState } from 'expo-audio';
import { File } from 'expo-file-system';

export default function VoiceRecorder({ onRecordingChange, onAudioReady }: {
  onRecordingChange: (recording: boolean) => void;
  onAudioReady: (uri: string) => Promise<boolean>;
}) {
  const recorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY);
  const recorderState = useAudioRecorderState(recorder);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const startedAt = useRef(0);
  const stopping = useRef(false);
  const [recording, setRecording] = useState(false);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState('');
  const [message, setMessage] = useState('');

  const stop = async () => {
    if (stopping.current) return;
    stopping.current = true;
    if (timer.current) clearTimeout(timer.current);
    setBusy(true);
    let file: File | null = null;
    try {
      const duration = recorder.getStatus().durationMillis || Date.now() - startedAt.current;
      if (recorder.isRecording) await recorder.stop();
      setRecording(false);
      if (!recorder.uri) throw new Error('No se generó el archivo de audio');
      file = new File(recorder.uri);
      if (!file.exists || file.size === 0) throw new Error('La grabación está vacía');
      if (file.size > 10 * 1024 * 1024) throw new Error('El audio supera 10 MB');
      const summary = `${Math.min(30, Math.max(1, Math.round(duration / 1000)))} s · ${file.extension} · ${Math.ceil(file.size / 1024)} KB`;
      const recognized = await onAudioReady(file.uri);
      setResult(recognized ? `Audio transcrito: ${summary}` : `No se reconoció texto: ${summary}`);
      setMessage('');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'No se pudo comprobar el audio');
    } finally {
      if (file?.exists) {
        try {
          file.delete();
          setResult((current) => `${current}${current ? '. ' : ''}Archivo borrado`);
        } catch {
          setMessage('No se pudo borrar el audio temporal. Cierra la app y elimina sus datos locales.');
        }
      }
      setRecording(false);
      onRecordingChange(false);
      setBusy(false);
      stopping.current = false;
    }
  };

  const start = async () => {
    if (busy || recording) return;
    setBusy(true); setMessage(''); setResult('');
    try {
      const permission = await AudioModule.requestRecordingPermissionsAsync();
      if (!permission.granted) throw new Error('Permite usar el micrófono para hacer esta prueba');
      await setAudioModeAsync({ playsInSilentMode: true, allowsRecording: true });
      await recorder.prepareToRecordAsync();
      recorder.record({ forDuration: 30 });
      startedAt.current = Date.now();
      setRecording(true);
      onRecordingChange(true);
      timer.current = setTimeout(() => { void stop(); }, 30000);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'No se pudo iniciar la grabación');
    } finally { setBusy(false); }
  };

  return <View style={styles.box}>
    <Text style={styles.title}>Reporte mediante voz</Text>
    <Text style={styles.note}>Describe un problema ficticio durante 5 a 10 segundos. La transcripción reemplazará la descripción actual para que puedas corregirla. El audio se borra al terminar.</Text>
    {recording && <Text style={styles.status}>Grabando: {Math.min(30, Math.floor(recorderState.durationMillis / 1000))}/30 s</Text>}
    <Button title={recording ? 'Detener y transcribir' : 'Iniciar grabación'} onPress={recording ? stop : start} disabled={busy} />
    {busy && !recording ? <Text style={styles.status}>Transcribiendo en el servidor local...</Text> : null}
    {result ? <Text style={styles.result}>{result}</Text> : null}
    {message ? <Text style={styles.error}>{message}</Text> : null}
  </View>;
}

const styles = StyleSheet.create({
  box: { borderWidth: 1, borderColor: '#aebbc5', borderRadius: 8, padding: 16, marginBottom: 12 },
  title: { fontSize: 18, fontWeight: '700', color: '#14324a' },
  note: { color: '#53636f', lineHeight: 20, marginVertical: 10 },
  status: { color: '#0866a3', fontWeight: '600', marginBottom: 8 },
  result: { color: '#27633d', marginTop: 10 },
  error: { color: '#a52828', marginTop: 10 },
});
