import numpy as np
import tensorflow as tf
import json

m = tf.saved_model.load('../ml/models/dynamic_classifier')
lm = json.load(open('../ml/models/dynamic_classifier/label_map.json'))

# Test 1: random input, training=True (default)
x = tf.constant(np.random.randn(1, 45, 258).astype('float32'))
out = m(x)
idx = int(out.numpy().argmax())
print(f"Random input (default): class {idx} = {lm[str(idx)]}, conf={float(out.numpy().max()):.3f}")

# Test 2: random input, training=False
out2 = m(x, training=False)
idx2 = int(out2.numpy().argmax())
print(f"Random input (training=False): class {idx2} = {lm[str(idx2)]}, conf={float(out2.numpy().max()):.3f}")

# Test 3: zeros input
x_zeros = tf.constant(np.zeros((1, 45, 258), dtype='float32'))
out3 = m(x_zeros, training=False)
idx3 = int(out3.numpy().argmax())
print(f"Zeros input (training=False): class {idx3} = {lm[str(idx3)]}, conf={float(out3.numpy().max()):.3f}")

# Top 5 for zeros
top5 = out3.numpy()[0].argsort()[::-1][:5]
print("Top 5 for zero input:", [(lm[str(i)], f"{out3.numpy()[0][i]:.3f}") for i in top5])
