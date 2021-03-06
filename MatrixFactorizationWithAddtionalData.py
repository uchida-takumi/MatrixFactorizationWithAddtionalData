#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Matrix Factorization which does not learns only UI-matrix but also attributes.
"""

import numpy as np
import sys
from sub_module import util


class MF:

    def __init__(self, n_latent_factor=200, learning_rate=0.005, 
                 regularization_weight=0.02, n_epochs=20, 
                 global_bias=True, id_bias=True,
                 verbose=False, random_seed=None):
        """
        Collabolative Filtering so called Matrix Factorization.
        
        Arguments:
            - n_latent_factor [int]: 
                number of latent dimensions
            - learning_rate [float]: 
                learning rate
            - regularization_weight [float]: 
                regularization parameter
            - global_bias [True/False]:
                set bias of global.
            - id_bias [True/False]:
                set bias of user_id, item_id.
            - n_epochs [int]: 
                number of epoch of train(SGD)
            - random_seed [int]: 
                random seed to set in np.random.seed()
        """
        
        # set random_seed
        if random_seed:
            np.random.seed(random_seed)

        self.n_latent_factor = n_latent_factor        
        self.learning_rate = learning_rate
        self.regularization_weight = regularization_weight
        self.global_bias = global_bias
        self.id_bias = id_bias
        self.n_epochs = n_epochs
        self.verbose = verbose            
        
    def fit(self, user_ids, item_ids, ratings, 
            user_attributes=None, item_attributes=None):            
        """
        Arguments:
            - user_ids [array-like-object]: 
                the array of user id.
            - item_ids [array-like-object]: 
                the array of item id.
            - ratings [array-like-object]: 
                the array of rating.
            - user_attributes [dictinary]:
                dictinary which key is user_id and value is vector of user attributes.
                if None, doesn't train on the attributes.
                ex) {'user00' : [0,1,0], 'user01': [.5,0,.5]]}
            - item_attributes [dictinary]:
                dictinary which key is item_id and value is vector of item attributes.
                if None, doesn't train on the attributes.
                ex) {'item00' : [0,1,0], 'item01': [.5,0,.5]]}
        """
        # Set up before fit
        self._fit_setup(
                user_ids, item_ids, ratings, 
                user_attributes, item_attributes
                )
        
        # Initialize coefficents of attributes.
        if user_attributes:
            self.a_u = np.zeros(self.n_dim_user_attributes, np.double)
        if item_attributes:
            self.a_i = np.zeros(self.n_dim_item_attributes, np.double)

        # Initialize the biases
        if self.global_bias:
            self.b = np.sum([r[2] for r in self.R])

        if self.id_bias:
            self.b_u = np.zeros(self.num_users, np.double)
            self.b_i = np.zeros(self.num_items, np.double)
        
        # Initialize user and item latent feature matrice
        if self.n_latent_factor:
            self.P = np.random.normal(0, scale=.1, size=(self.num_users, self.n_latent_factor))
            self.Q = np.random.normal(0, scale=.1, size=(self.num_items, self.n_latent_factor))

        # Perform stochastic gradient descent for number of iterations
        before_mse = sys.maxsize
        stop_cnt = 0 
        for i in range(self.n_epochs):

            # update parametors
            self.sgd()

            mse = self.mse()            
            if ((i+1) % 10 == 0) and self.verbose:
                print("Iteration: %d ; error(MAE) = %.4f ; learn_rate = %.4f ;" % (i+1, mse, self.learning_rate))
            
            # if error improve rate is not enough, update self.learning_rate lower.
            mse_improve_rate = (before_mse-mse)/before_mse if before_mse>0 else 0
            if  mse_improve_rate < 1e-8 :
                self.learning_rate *= 0.5
                stop_cnt += 1
            # if stop_cnt is more than a threshold, stop training.
            if stop_cnt > 10:
                break
            
            before_mse = mse
        
        return self
    
    def _fit_setup(self, user_ids, item_ids, ratings, 
                   user_attributes, item_attributes):
        """
        transform user_ids and item_ids to the incremental index.
        
        Arguments example:
            user_ids = [1,1,2]
            item_ids = [0,5,0]
            ratings  = [3,3,4]
            user_attributes = {1:[0,1,1], 2:[0,0,1]}
            item_attributes = {0:[0,1], 5:[1,1]}
        """
        # set id transformer
        user_ids_transformer = util.id_transformer()
        item_ids_transformer = util.id_transformer()        
        transformed_user_ids = user_ids_transformer.fit_transform(user_ids)
        transformed_item_ids = item_ids_transformer.fit_transform(item_ids)        
        self.user_ids_transformer = user_ids_transformer
        self.item_ids_transformer = item_ids_transformer
        
        # put parameters pn self
        self.R = [(u,i,r) for u,i,r in zip(transformed_user_ids, transformed_item_ids, ratings)]
        self.num_users, self.num_items = len(set(transformed_user_ids)), len(set(transformed_item_ids))
        
        # change attributes to numpy.array as UserAttribute, ItemAttribute
        if user_attributes:
            self.n_dim_user_attributes = len(list(user_attributes.values())[0])
            self.UserAttr = np.zeros(shape=[self.num_users, self.n_dim_user_attributes])
            for _id,attr in user_attributes.items():
                transformed_id = self.user_ids_transformer.transform([_id], unknown=None)[0]
                if transformed_id is not None:
                    self.UserAttr[transformed_id, :] = attr
            self.fit_user_attributes = True
        else:
            self.fit_user_attributes = False
                        
        if item_attributes:
            self.n_dim_item_attributes = len(list(item_attributes.values())[0])
            self.ItemAttr = np.zeros(shape=[self.num_items, self.n_dim_item_attributes])
            for _id,attr in item_attributes.items():
                transformed_id = self.item_ids_transformer.transform([_id], unknown=None)[0]
                if transformed_id is not None:
                    self.ItemAttr[transformed_id, :] = attr
            self.fit_item_attributes = True
        else:
            self.fit_item_attributes = False
            
        

    def predict(self, user_ids, item_ids, user_attributes=dict(), item_attributes=dict()):
        """
        Arguments:
            user_ids [array-like object]:
                pass
            item_ids [array-like object]:
                pass
            user_attributes [dict]:
                pass
            item_attributes [dict]:
                pass
        """
        # check argument.
        if (self.fit_user_attributes) and (user_attributes==dict()):
            raise 'This instance has be fitted using user_attributes, but no attributes in the arguments.' 
        if (self.fit_item_attributes) and (item_attributes==dict()):
            raise 'This instance has be fitted using item_attributes, but no attributes in the arguments.' 
        
        # predict
        results = []
        for u,i in zip(user_ids, item_ids):
            tf_u = self.user_ids_transformer.transform([u], unknown=None)[0]
            tf_i = self.item_ids_transformer.transform([i], unknown=None)[0]

            user_attr = user_attributes.get(u, None)
            if (user_attr is None) and (self.fit_user_attributes):
                user_attr = self.UserAttr[tf_u]

            item_attr = item_attributes.get(i, None)
            if (item_attr is None) and (self.fit_item_attributes):
                item_attr = self.ItemAttr[tf_i]

            results.append(self._predict(tf_u, tf_i, user_attr, item_attr))

        return np.array(results)
    

    def mse(self):
        """
        A function to compute the total mean square error
        """
        user_ids, item_ids, ratings = [], [], []
        for u,i,r in self.R:
            user_ids.append(u)
            item_ids.append(i)
            ratings.append(r)
        
        error = 0
        for u,i,r in self.R:
            user_attr = self.UserAttr[u] if self.fit_user_attributes else None
            item_attr = self.ItemAttr[i] if self.fit_item_attributes else None
            predicted = self._predict(u, i, user_attr, item_attr)
            error += pow(r - predicted, 2)
        return np.sqrt(error)


    def sgd(self):
        """
        Perform stochastic graident descent
        """
        for u,i,r in self.R:
            # Computer prediction and error
            user_attr = self.UserAttr[u] if self.fit_user_attributes else None
            item_attr = self.ItemAttr[i] if self.fit_item_attributes else None
            e = r - self._predict(u, i, user_attr, item_attr)
            
            # Update attribute coefficient
            if self.fit_user_attributes:
                self.a_u += self.learning_rate * self.UserAttr[u]  * (e - self.regularization_weight * self.a_u)
            if self.fit_item_attributes:
                self.a_i += self.learning_rate * self.ItemAttr[i]  * (e - self.regularization_weight * self.a_i)

            # Update biases
            if self.id_bias:
                self.b_u[u] += self.learning_rate * (e - self.regularization_weight * self.b_u[u])
                self.b_i[i] += self.learning_rate * (e - self.regularization_weight * self.b_i[i])

            # Update user and item latent feature matrices
            if self.n_latent_factor:
                self.P[u, :] += self.learning_rate * (e * self.Q[i, :] - self.regularization_weight * self.P[u,:])
                self.Q[i, :] += self.learning_rate * (e * self.P[u, :] - self.regularization_weight * self.Q[i,:])
        

    def _predict(self, u, i, user_attr=None, item_attr=None):
        """
        Get the predicted rating of user u and item i.
        user_attr [np.array] is vector of user attributes.
        item_attr [np.array] in vector of item attributes.
        """
        prediction = 0

        # global bias
        if self.global_bias:
            prediction += self.b

        # user_id bias, item_id bias
        if self.id_bias:
            if u is not None:
                prediction += self.b_u[u]
            if i is not None:
                prediction += self.b_i[i]

        # attributes 
        if (self.fit_user_attributes) and (user_attr is not None):
            prediction += (self.a_u * user_attr).sum()
        if (self.fit_item_attributes) and (item_attr is not None):
            prediction += (self.a_i * item_attr).sum()
        
        # latent factor
        if self.n_latent_factor:
            if (u is not None) and (i is not None):
                prediction += np.dot(self.P[u, :], self.Q[i, :].T)

        return prediction
    

if __name__ == 'how to use':

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
