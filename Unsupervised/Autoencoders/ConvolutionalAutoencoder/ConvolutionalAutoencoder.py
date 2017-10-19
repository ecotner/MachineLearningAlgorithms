# -*- coding: utf-8 -*-
"""
Created on Wed Oct 18 21:46:33 2017

An autoencoder that takes an image as input, then finds a lower-dimensional representation of it in order to learn some generally applicable features. Testing with the MNIST dataset.

@author: Eric Cotner
"""

import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt

''' ======================== SET UP COMPUTATIONAL GRAPH ================== '''

def initialize_graph():
    tf.reset_default_graph()
    G = tf.Graph()
    
    with G.as_default():
        
        # Input layer
        X = tf.placeholder(tf.float32, shape=[None,28,28,1], name='X')
        
        # Convolutional layers
        c_in, c_out = (1,16)
        W1 = tf.Variable(np.random.randn(5,5,c_in,c_out)*np.sqrt(2/(5*5*c_in+c_out)), dtype=tf.float32, name='W1')
        b1 = tf.Variable(np.zeros((c_out,)), dtype=tf.float32, name='b1')
        conv1 = tf.nn.relu(tf.nn.conv2d(X, W1, strides=[1,1,1,1], padding='VALID') + b1, name='conv1')
        (pool1, pool1_arg) = tf.nn.max_pool_with_argmax(conv1, ksize=[1,2,2,1], strides=[1,2,2,1], padding='VALID')
        # Output from pool1 should be [None,12,12,c_out]
        
        c_in, c_out = (c_out,16)
        W2 = tf.Variable(np.random.randn(4,4,c_in,c_out)*np.sqrt(2/(4*4*c_in+c_out)), dtype=tf.float32, name='W2')
        b2 = tf.Variable(np.zeros((c_out,)), dtype=tf.float32, name='b2')
        conv2 = tf.nn.relu(tf.nn.conv2d(pool1, W2, strides=[1,2,2,1], padding='VALID') + b2, name='conv2')
        # Output from conv2 should be [None,5,5,c_out]
        
        # Deconvolutional layers
        c_in, c_out = (c_out,16)
        W3 = tf.Variable(np.random.randn(4,4,c_out,c_in)*np.sqrt(2/(4*4*c_in+c_out)), dtype=tf.float32, name='W3')
        b3 = tf.Variable(np.zeros((c_out,)), dtype=tf.float32, name='b3')
        deconv3 = tf.nn.relu(tf.nn.conv2d_transpose(conv2, W3, output_shape=[None,12,12,c_out], strides=[1,2,2,1], padding='VALID') + b3, name='deconv3')
        # Output from deconv3 should be [None,12,12,c_out]
        
        c_in, c_out = (c_out, 1)
        W4 = tf.Variable(np.random.randn(6,6,c_out,c_in)*np.sqrt(2/(6*6*c_in+c_out)), dtype=tf.float32, name='W4')
        b4 = tf.Variable(np.zeros((c_out,)), dtype=tf.float32, name='b4')
        Y = tf.nn.conv2d_transpose(deconv3, W4, output_shape=[None,28,28,c_out], strides=[1,2,2,1], padding='VALID', name='Y')
        
        # Loss function is MSE of difference between input and output
        loss = tf.reduce_mean((X-Y)**2, name='loss')
    
    # Return Graph
    return G

''' ========================== TRAIN AUTOENCODER ======================== '''

def make_minibatches(X, batch_size, batch_axis=0):
    batches = []
    m = X.shape[batch_axis]
    perm_idx = np.random.permutation(m)
    X_perm = X[perm_idx,:,:,:]
    for b in range(m//batch_size):
        minibatch = X_perm[b*batch_size:(b+1)*batch_size,:,:,:]
        batches.append(minibatch)
    if m % batch_size != 0:
        minibatch = X_perm[(b+1)*batch_size:,:,:,:]
        batches.append(minibatch)
    return batches

def train_model(X_train, lr, max_epochs, X_val=None, reload_parameters=False, save_path=None, plot_every_n_steps=25, save_every_n_epochs=2):
    # Build the computational graph
    G = initialize_graph()
    with G.as_default():
        # Define dict of useful tensors
        cae = {'X':G.get_tensor_by_name('X:0'),
               'Z':G.get_tensor_by_name('conv2:0'),
               'Y':G.get_tensor_by_name('Y:0'),
               'loss':G.get_tensor_by_name('loss:0')}
        # Define the optimizer and training operation
        optimizer = tf.train.AdamOptimizer(lr)
        train_op = optimizer.minimize(cae['loss'])
        # Define Saver
        saver = tf.train.Saver()
        # Make minibatches
        minibatches = make_minibatches(X_train, batch_size=32, batch_axis=0)
        # Create TF Session
        with tf.Session() as sess:
            # Initialize variables or load parameters
            if reload_parameters == True:
                saver.restore(sess, save_path)
            else:
                sess.run(tf.global_variables_initializer())
            # Define training metric lists to track
            loss_list = []
            step_list = []
            val_loss_list = []
            # Iterate over epochs
            global_step = 0
            nan_flag = False
            for ep in range(max_epochs):
                # Iterate over minibatches
                for b, batch in enumerate(minibatches):
                    global_step += 1
                    # Get loss, perform training op
                    _, loss = sess.run([train_op, cae['loss']], 
                                       feed_dict={cae['X']:batch})
                    # Exit if nan
                    if loss == np.nan:
                        print('nan error, exiting training')
                        nan_flag = True
                        break
                    # Plot progress
                    if global_step % plot_every_n_steps == 0:
                        loss_list.append(loss)
                        step_list.append(global_step/len(minibatches))
                        plt.figure('Loss')
                        plt.clf()
                        plt.semilogy(step_list, loss_list, label='Training')
                        if X_val is not None:
                            val_loss = sess.run(loss, feed_dict={cae['X']:X_val})
                            val_loss_list.append(val_loss)
                            plt.semilogy(step_list, val_loss_list, label='Validation')
                            plt.legend()
                        plt.title('Batch loss during training')
                        plt.xlabel('Epoch')
                        plt.ylabel('Avg loss')
                # Save parameters
                if nan_flag == True:
                    break
                elif ep % save_every_n_epochs == 0:
                    print('Saving...')
                    saver.save(sess, save_path)
            # Save at end
            print('Saving...')
            saver.save(sess, save_path)
            print('Training complete!')

































