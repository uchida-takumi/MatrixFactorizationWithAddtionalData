#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# set training data
user_ids = [1,1,1,1,5,5,8,8]
item_ids = [1,2,3,4,2,4,1,2]
ratings  = [5,5,4,4,3,3,2,2]
user_attributes = {1:[0,1,1], 5:[1,1,0], 8:[0,0,1]}
item_attributes = {1:[1.2, 2.3], 99:[3.7, 1.1]}

# load module
from MatrixFactorizationWithAddtionalData import MF

# train
n_epochs = 10000
mf = MF(n_latent_factor=2, learning_rate=0.005, regularization_weight=0.02, n_epochs=n_epochs, verbose=True)
mf.fit(user_ids, item_ids, ratings, user_attributes, item_attributes)

# predict on insample
preidict = mf.predict(
            user_ids, item_ids, 
            user_attributes=user_attributes,
            item_attributes=item_attributes
            )
print(preidict)
    

# predict on outsample
preidict = mf.predict(
            user_ids=[8,8,8], item_ids=[3,4,99], 
            user_attributes=user_attributes,
            item_attributes=item_attributes
            )
print(preidict)
