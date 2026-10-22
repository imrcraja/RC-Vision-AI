# Image research dataset

Place at least two images you own or have explicit permission to use under this directory to enable the optional daily image-reconstruction experiment. Supported formats: PNG, JPG/JPEG, WebP, BMP. Keep private images out of the public repository.

The initial `training/image/train_autoencoder.py` implementation trains a tiny convolutional autoencoder from random initialization to reconstruct 64×64 RGB images. It is deliberately **not** described as a prompt-conditioned image generator: it has no text encoder, no prompt/image alignment objective, and no semantic generation guarantee. The workflow skips image training when fewer than two images are present.

Before adding a real dataset, document source, creator, permission/license, collection date, and a content hash. Never add secrets or private photos without consent. Dataset images committed to a public repository may become publicly accessible.
