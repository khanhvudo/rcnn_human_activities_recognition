#!/usr/bin/env python3
'''
This script will randomize weights and train the tiny yolo from scratch.
'''
from datahandler import get_batch
import tensorflow as tf
import numpy as np
import os
import sys
import shutil
import time

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

saver = tf.train.import_meta_graph("./graph/tiny-yolo.ckpt.meta")
with tf.Session() as sess:
    saver.restore(sess, "./graph/tiny-yolo.ckpt")
    g = sess.graph
    with g.name_scope("TRAINER"):
        X = g.get_tensor_by_name("YOLO/input:0")
        batch_size, height, width, in_channels = X.get_shape().as_list()
        classes = 4
        out_height = height//32
        out_width = width//32
        # out_channels = 3*(5+classes)
        out_channels = 5+classes
        h1 = g.get_tensor_by_name("YOLO/output1:0")
        # h2 = g.get_tensor_by_name("YOLO/output2:0")
        Y1 = tf.placeholder(shape = (batch_size, out_height, out_width, out_channels), dtype = tf.float32, name = "groundtruth1")
        # Y2 = tf.placeholder(shape = (batch_size, 2*out_height, 2*out_width, out_channels), dtype = tf.float32, name = "groundtruth2")
    
        #loss
        #loss
        h = tf.reshape(h1, [batch_size * out_height * out_width, out_channels], name='h')
        Y = tf.reshape(Y1, [batch_size * out_height * out_width, out_channels], name='Y')

        Lcoord = 5
        Lnoobj = 0.5
        loss_xy = Lcoord*tf.reduce_mean(Y[:,0]*((h[:,1] - Y[:,1])**2 + (h[:,2] - Y[:,2])**2))
        loss_wh = Lcoord*tf.reduce_mean(Y[:,0]*((h[:,3]**0.5 - Y[:,3]**0.5)**2+(h[:,4]**0.5 - Y[:,4]**0.5)**2))
        loss_obj = (-1)*tf.reduce_mean(tf.tile(Y[:,0:1], (1, classes))*(Y[:,5:]*tf.log(h[:,5:]) + (1-Y[:,5:])*tf.log(1-h[:,5:])))
        loss_noobj = (-1*Lnoobj)*tf.reduce_mean(tf.tile(1-Y[:,0:1], (1, classes))*(Y[:,5:]*tf.log(h[:,5:]) + (1-Y[:,5:])*tf.log(1-h[:,5:])))
        loss_p = (-1)*tf.reduce_mean(tf.tile(Y[:,0:1], (1, classes))*tf.log((tf.tile(h[:,0:1], (1, classes)) * Y[:,5:])) + (1-tf.tile(Y[:,0:1], (1, classes)))*tf.log(1-(tf.tile(h[:,0:1], (1, classes)) * Y[:,5:])))

        loss = loss_xy + loss_wh + loss_obj + loss_noobj + loss_p

        optimizer = tf.train.AdamOptimizer(learning_rate = 1e-3)
        trainer = optimizer.minimize(loss, name = "trainer")

    if os.path.exists("./train_graph"):
            shutil.rmtree("./train_graph")
    os.mkdir("./train_graph")

    train_writer = tf.summary.FileWriter("./train_graph", g)
    saver = tf.train.Saver()
    tf.summary.histogram("loss", loss)
    merge = tf.summary.merge_all()


    sess.run(tf.global_variables_initializer())

    input_size = height

    #for batch in shuffle(batch_size, input_size):
    epoch = 0
    while epoch < 100:
        loss_total = 0.
        acc_total = 0.
        for batch in get_batch(batch_size, input_size):
            step, Xp, Y1p = batch
            if step == 0:
                time.sleep(1)
                continue
            debugger = tf.logical_or(tf.is_nan(loss), tf.is_inf(loss))

            while (1):
                d, l = sess.run([debugger, loss], 
                    feed_dict = {X:Xp, Y1:Y1p})
                if (not d):
                    break
                else:
                    print("Re-random variables!")
                    sess.run(tf.global_variables_initializer())
            summary, _ , lossp, lxy, lwh, lobj, lnoobj, lp = sess.run(
                        [merge, trainer, loss, loss_xy, loss_wh, loss_obj, loss_noobj, loss_p],
                        feed_dict = {X: Xp, Y1: Y1p})

            loss_total += lossp
            print("""Step {} : loss {}
                            loss_xy     = {}
                            loss_wh     = {}
                            loss_obj    = {}
                            loss_noobj  = {}
                            loss_p      = {}\n""".format(step, lossp, lxy, lwh, lobj, lnoobj, lp), end="\n")

            train_writer.add_summary(summary, step)

        print("""Epoch {}: loss_avg {}; acc_avg {}\n""".format(epoch, loss_total/step, acc_total/step))
        epoch += 1

        if (epoch % 10 == 0):
            saver.save(sess, "./train_graph/tiny-yolo-{}.ckpt".format(epoch))

    print("Training done!!!")

