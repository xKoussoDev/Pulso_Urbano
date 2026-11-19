import { useRef, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { AudioModule, RecordingPresets, setAudioModeAsync, useAudioRecorder, useAudioRecorderState } from 'expo-audio';
import { File } from 'expo-file-system';
import { colors, space } from './theme';
import { ActionButton, LoadingMark } from './ui';

export default function VoiceRecorder({ onRecordingChange, onAudioReady }: {
  onRecordingChange: (recording: boolean) => void;
  onAudioReady: (uri: string) => Promise<boolean>;
}) {
  const recorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY);
  const recorderState = useAudioRecorderState(recorder);
  const maxSeconds = 10;
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const stopping = useRef(false);
  const [recording, setRecording] = useState(false);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState('');
  const [message, setMessage] = useState('');

  const cancel = async () => {
    if (stopping.current || busy) return;
    stopping.current = true;
    if (timer.current) clearTimeout(timer.current);
    timer.current = null;
    try {
      if (recorder.isRecording) await recorder.stop();
      if (recorder.uri) {
        const file = new File(recorder.uri);
        if (file.exists) file.delete();
      }
      setMessage('Grabación cancelada');
    } catch {
      setMessage('No se pudo cancelar la grabación');
    } finally {
      setRecording(false);
      onRecordingChange(false);
      stopping.current = false;
    }
  };

  const stop = async () => {
    if (stopping.current) return;
    stopping.current = true;
    if (timer.current) clearTimeout(timer.current);
    timer.current = null;
    setBusy(true);
    let file: File | null = null;
    try {
      if (recorder.isRecording) await recorder.stop();
      setRecording(false);
      if (!recorder.uri) throw new Error('No se generó el archivo de audio');
      file = new File(recorder.uri);
      if (!file.exists || file.size === 0) throw new Error('La grabación está vacía');
      if (file.size > 10 * 1024 * 1024) throw new Error('El audio supera 10 MB');
      const recognized = await onAudioReady(file.uri);
      setResult(recognized ? 'Texto listo para revisar' : 'No se reconoció el audio. Escribe el reporte.');
      setMessage('');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'No se pudo comprobar el audio');
    } finally {
      if (file?.exists) {
        try {
          file.delete();
          setResult((current) => `${current}${current ? '. ' : ''}Audio borrado`);
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
      if (!permission.granted) throw new Error('Permite usar el micrófono para grabar');
      await setAudioModeAsync({ playsInSilentMode: true, allowsRecording: true });
      await recorder.prepareToRecordAsync();
      recorder.record({ forDuration: maxSeconds });
      setRecording(true);
      onRecordingChange(true);
      timer.current = setTimeout(() => { void stop(); }, maxSeconds * 1000);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'No se pudo iniciar la grabación');
    } finally { setBusy(false); }
  };

  return <View style={styles.box}>
    <Text style={styles.title}>Cuéntanos qué pasó</Text>
    <Text style={styles.note}>Graba hasta 10 segundos. Después podrás corregir el texto.</Text>
    {recording && <Text style={styles.status} accessibilityLiveRegion="polite">● Grabando · {Math.min(maxSeconds, Math.floor(recorderState.durationMillis / 1000))} de {maxSeconds} segundos</Text>}
    <ActionButton title={recording ? 'Detener y transcribir' : 'Cuéntanos qué pasó'} variant="secondary"
      onPress={recording ? () => { void stop(); } : () => { void start(); }} disabled={busy} />
    {recording ? <View style={{ marginTop: space.sm }}><ActionButton title="Cancelar grabación" variant="danger" onPress={() => { void cancel(); }} disabled={busy} /></View> : null}
    {busy && !recording ? <LoadingMark label="Transcribiendo tu reporte…" /> : null}
    {result ? <Text style={styles.result}>{result}</Text> : null}
    {message ? <Text style={styles.error} accessibilityRole="alert">{message}</Text> : null}
  </View>;
}

const styles = StyleSheet.create({
  box: { backgroundColor: colors.softBlue, borderRadius: 14, padding: space.md, marginTop: space.md },
  title: { fontSize: 17, fontWeight: '800', color: colors.ink },
  note: { color: colors.muted, fontSize: 15, lineHeight: 21, marginVertical: space.sm },
  status: { color: colors.primary, fontSize: 16, fontWeight: '700', marginBottom: space.sm },
  result: { color: colors.success, fontSize: 15, marginTop: space.sm },
  error: { color: colors.danger, fontSize: 15, marginTop: space.sm },
});
