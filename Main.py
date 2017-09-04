import os
import sys
import time
import cPickle as pickle
import pyaudio
from scipy.io import wavfile

from collections import defaultdict
import BOB as MFCC
import LPC
import numpy as np
import traceback as tb
from ActivityDetection import ActivityDetection

try:
    from gmmset import GMMSetPyGMM as GMMSet
    from gmmset import GMM
except Exception as e:
    print >> sys.stderr, "Warning: failed to import fast-gmm, use gmm from scikit-learn instead"
    print str(e)
    from skgmm import GMMSet, GMM

class Main():
    
    FORMAT=pyaudio.paInt16
    NPDtype = 'int16'
    FS=8000

    model_file = '02-09-2017.model'
    
    def __init__(self):
        self.features = defaultdict(list)
        self.gmmset = GMMSet()
        self.ad = ActivityDetection()
        self.signal = []
        fs, signal = wavfile.read('background earphone.wav')
        self.ad.init_noise(fs, signal)
        
    def getFeatures(self):
        '''
        mfcc = MFCC.extract(self.FS, self.signal)
        lpc = LPC.extract(self.FS, self.signal)
        features = np.concatenate((mfcc, lpc), axis=1) 
        '''
        features = self.mix_feature()
        self.features[self.name].extend(features)
        return features

    def mix_feature(self):
        mfcc = MFCC.extract(self.FS, self.signal)
        lpc = LPC.extract(self.FS, self.signal)
        #if len(mfcc) == 0:
        #    print >> sys.stderr, "ERROR.. failed to extract mfcc feature:", len(tup[1])
        #print "mfcc ",mfcc
        #print "lpc ",lpc
        return np.concatenate((mfcc, lpc), axis=1)

    def _get_gmm_set(self):
        '''
        if os.path.isfile(self.ubm_model_file):
            try:
                from gmmset import GMMSetPyGMM
                if GMMSet is GMMSetPyGMM:
                    return GMMSet(ubm=GMM.load(self.model_file))
            except Exception as e:
                print "Warning: failed to import gmmset. You may forget to compile gmm:"
                print e
                print "Try running `make -C src/gmm` to compile gmm module."
                print "But gmm from sklearn will work as well! Using it now!"
            return GMMSet()
        '''
        return GMMSet()

    def train(self):
        self.gmmset = self._get_gmm_set()
        start = time.time()
        print "Training start..."
        for name, feats in self.features.iteritems():
            self.gmmset.fit_new(feats, name)
        print time.time() - start, " seconds"
        print "Training complete"

    def predict(self):
        """ return a label (name)"""
        try:
            features = self.mix_feature()
        except Exception as e:
            print tb.format_exc()
            return None
        #print 'The registered users are :', len(self.gmmset.y)
        #print self.gmmset.y
        #print [y for y in self.gmmset.y]
        return self.gmmset.predict_one(features)

    def dump(self):
        """ dump all models to file"""
        self.gmmset.before_pickle()
        with open(self.model_file, 'w') as f:
            pickle.dump(self, f, -1)
        self.gmmset.after_pickle()

    @staticmethod
    def load(fname):
        """ load from a dumped model file"""
        with open(fname, 'r') as f:
            m = pickle.load(f)
            m.gmmset.after_pickle()
            return m

