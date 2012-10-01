#!/usr/bin/env python       
# Software License Agreement (BSD License)
#
# Copyright (c) 2012, Yujin Robot, Daniel Stonier, Jihoon Lee
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Yujin Robot nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import rospy
import threading
import rosmaster
import rosnode
import rosgraph

class WatcherThread(threading.Thread):

  def __init__(self,gateway_sync):
    # init thread
    threading.Thread.__init__(self)
    self.gateway_sync = gateway_sync
    self.ros_manager = gateway_sync.ros_manager
    self.master = self.ros_manager.master
    self.cv = self.ros_manager.cv
    self.pubs = self.ros_manager.pubs_node
    self.public_interface = self.ros_manager.public_interface

    # dumped interface is a mapping of whitelist regex to actual topics as they
    # become available
    self.dumped_interface = dict()
    self.dumped_interface['topic'] = set()
    self.dumped_interface['service'] = set()

    self.start()

  def run(self):
 
    print "Thread Started"

    while not rospy.is_shutdown():
      self.cv.acquire()

#      self.checkRemoteList()
      if self.gateway_sync.connected: 
        # 1. Check all remove interfaces are still in redis server, if it is gone, unregister it
#self.pollServer()


        # 2. Check all local public interfaces are still valid
        self.checkPublicInterfaces()
      self.cv.release()
      rospy.sleep(3.0)

  def pollServer(self):
    remotelist = self.gateway_sync.getRemoteLists()

    for master in remotelist:
      print str(remotelist[master])


  def checkPublicInterfaces(self):
    pubs, _, srvs = self.master.getSystemState() 
  
    self.update("topic",pubs)
    self.update("service",srvs)

  def update(self,identifier,list):
    for string in self.public_interface[identifier]:
      name, _, node_uri = string.split(",")
      still_exist = False
      try:
        llist = [x[1] for x in list if x[0] == name]

        # all nodes are gone.
        uris = [self.master.lookupNode(p) for p in llist[0]]
        still_exist = node_uri in uris
      except: 
        still_exist = False
        
      # if it is not exist anymore, remove it from public interface
      if not still_exist:
        self.gateway_sync.removePublicInterface(identifier,string)

    # add/remove named interfaces as necessary
    for x in list:
      name = x[0]
      if self.gateway_sync.allowInterfaceInDump(identifier, name):
        # check if any new publishers are available
        self.gateway_sync.addPublicInterfaceByName(identifier, name)
        self.dumped_interface[identifier].add(name)
      else:
        # this interface has been dumped in the past, and is no longer needed
        if name in self.dumped_interface[identifier]:
          self.gateway_sync.removePublicInterfaceByName(identifier, name)
          self.dumped_interface[identifier].remove(name)

"""
  polling thread should do...
  1. unregister the unavailable remote topics/services
  2. remove the unavailable topics/services from public list
"""