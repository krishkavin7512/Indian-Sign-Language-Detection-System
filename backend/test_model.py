import numpy as np
import tensorflow as tf

print("Loading model...")
m = tf.saved_model.load('../ml/models/dynamic_classifier')
print("Model loaded OK")

x = tf.constant(np.random.randn(1, 45, 258).astype('float32'))
out = m(x)
print("Output shape:", out.shape)
print("Top prediction index:", int(out.numpy().argmax()))
print("Max confidence:", float(out.numpy().max()))
print("Model inference works!")
