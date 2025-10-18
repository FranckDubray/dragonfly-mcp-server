// AudioWorklet processor that forwards mono input frames to the main thread
class VADProcessor extends AudioWorkletProcessor {
  process(inputs, outputs, parameters) {
    const input = inputs[0];
    if (input && input[0] && input[0].length) {
      const ch = input[0]; // Float32Array of 128 frames (render quantum)
      // Copy to transferable buffer
      const buf = new Float32Array(ch.length);
      buf.set(ch);
      this.port.postMessage(buf, [buf.buffer]);
    }
    return true; // keep alive
  }
}
registerProcessor('vad-processor', VADProcessor);
