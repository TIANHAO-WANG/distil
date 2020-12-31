from .strategy import Strategy
import copy
import datetime
import numpy as np
import os
import subprocess
import sys
import time
import torch
import torch.backends.cudnn as cudnn
import torch.nn as nn
import torch.optim as optim
from torch.autograd import Variable
from torch.utils.data import DataLoader
from matplotlib import pyplot as plt
import math
import random
from torch.distributions import Categorical
from .set_function_craig import PerClassNonDeepSetFunction, PerClassDeepSetFunction

class FASS(Strategy):

    def __init__(self, X, Y, unlabeled_x, net, handler, nclasses, args):
        super(FASS, self).__init__(X, Y, unlabeled_x, net, handler,nclasses, args)

    def select(self, n):

        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        # idxs_unlabeled = np.arange(self.n_pool)[~self.idxs_lb]
        # print('Length of unlabeled ', len(idxs_unlabeled))
        curr_X_trn = self.unlabeled_x
        cached_state_dict = copy.deepcopy(self.net.state_dict())
        predicted_y = self.predict(curr_X_trn)  # Hypothesised Labels
        soft = self.predict_prob(curr_X_trn)    #Probabilities of each class

        entropy2 = Categorical(probs = soft).entropy()
        
        if 5*n < entropy2.shape[0]:
            values,indices = entropy2.topk(5*n)
        else:
            indices = [i for i in range(entropy2.shape[0])]    
        curr_X_trn = torch.from_numpy(curr_X_trn)

        #Handling image data, 3d to 2d
        if len(list(curr_X_trn.size())) == 3:
            curr_X_trn = torch.reshape(curr_X_trn, (curr_X_trn.shape[0], curr_X_trn.shape[1]*curr_X_trn.shape[2]))

        p_class_dsf = PerClassNonDeepSetFunction(device, curr_X_trn[indices], predicted_y[indices], self.net, curr_X_trn.shape[0], 32, True)
        dsf_idxs_flag_val, _ = p_class_dsf.lazy_greedy_max(n, cached_state_dict)

        #Mapping to original indices
        return_indices = []
        for val in dsf_idxs_flag_val:
            append_val = val
            return_indices.append(indices[append_val])
        return return_indices

# class FASS(Strategy):

#     def __init__(self, X, Y, idxs_lb, net, handler, args):
#         super(FASS, self).__init__(X, Y, idxs_lb, net, handler, args)

#     def query(self, n):

#         device = "cuda:0" if torch.cuda.is_available() else "cpu"
#         idxs_unlabeled = np.arange(self.n_pool)[~self.idxs_lb]
#         # print('Length of unlabeled ', len(idxs_unlabeled))
#         cached_state_dict = copy.deepcopy(self.net.state_dict())
#         curr_X_trn = self.X[idxs_unlabeled]
#         curr_y_trn = self.Y[idxs_unlabeled]
#         predicted_y = self.predict(curr_X_trn, curr_y_trn)  # Hypothesised Labels
#         soft = self.predict_prob(curr_X_trn, curr_y_trn)    #Probabilities of each class

#         entropy2 = Categorical(probs = soft).entropy()
#         if 5*n < entropy2.shape[0]:
#             values,indices = entropy2.topk(5*n)
#         else:
#             indices = [i for i in range(entropy2.shape[0])]    
#         curr_X_trn = torch.from_numpy(curr_X_trn)

#         #Handling image data, 3d to 2d
#         if len(list(curr_X_trn.size())) == 3:
#             curr_X_trn = torch.reshape(curr_X_trn, (curr_X_trn.shape[0], curr_X_trn.shape[1]*curr_X_trn.shape[2]))

#         p_class_dsf = PerClassNonDeepSetFunction(device, curr_X_trn[indices], predicted_y[indices], self.net, curr_X_trn.shape[0], 32, True)
#         dsf_idxs_flag_val, _ = p_class_dsf.lazy_greedy_max(n, cached_state_dict)

#         #Mapping to original indices
#         return_indices = []
#         for val in dsf_idxs_flag_val:
#             return_indices.append(idxs_unlabeled[indices[val]])

#         return return_indices
