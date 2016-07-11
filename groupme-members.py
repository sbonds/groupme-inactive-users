#!/usr/bin/env python

# Usage:
#  groupme-members.py <group number> > <group number>-members.csv
# Find a list of people who are members of a Groupme group
#
# Info needed:
# + API authentication token (OAuth requires a callback URL, and this isn't a web app so the token must be pulled from an active session.)
# + Group ID (also pulled from an active session)
#
# Method:
# + Retrieve member list of group: https://dev.groupme.com/docs/v3#groups_show
# ++ for user name to user id mapping
# ++ also shows group creator, which could be useful if a group needs to be enlarged

# How?
# + Python3 on CentOS 6
# ++ created user "groupme"
# ++ as that user:
# +++ curl -C - -O 'https://www.python.org/ftp/python/3.5.1/Python-3.5.1.tar.xz.asc'
# +++ curl -C - -O 'https://www.python.org/ftp/python/3.5.1/Python-3.5.1.tar.xz'
# +++ gpg --recv-keys 0xF73C700D
# +++ gpg --verify Python-3.5.1.tar.xz.asc
# +++ tar xJvf Python-3.5.1.tar.xz
# +++ cd Python-3.5.1
# +++ ./configure --prefix=$HOME
# +++ make
# +++ make test
# +++ make install
# +++ vi .bashrc (add /home/groupme/bin to PATH)
# +++ pip3 install GroupyAPI
#
# + https://pypi.python.org/pypi/GroupyAPI <-- Python abstraction of the GroupMe API, requires Python3
# ++ log in to https://dev.groupme.com/session/new and get token from that page (handy!)
# ++ put token in $HOME/.groupy.key file
#
# API exploration:
# >>> import groupy
# >>> groups=groupy.Group.list()
# >>> group=groups.first
# >>> dir(group)
#  'add', 'create', 'created_at', 'creator_user_id', 'description', 'destroy', 'group_id', 'id', 'image_url', 'last_message_created_at', 'last_message_id', 'list', 'max_members', 'members', 'message_count', 'messages', 'name', 'office_mode', 'phone_number', 'post', 'refresh', 'remove', 'share_url', 'type', 'update', 'updated_at'
# >>> members = groupy.Member.list()
# >>> dir(groupy.Member)
# 'guid', 'identification', 'identify', 'list', 'messages', 'post'
# (Doesn't look like anything to auto-create a dictionary of members by ID, so I'll plan to iterate the list)
# (Similarly, nothing seems to auto-create a dictionary of groups by ID, either.)
# >>> member=members.first
# >>> dir(member)
# 'app_installed', 'autokicked', 'guid', 'id', 'identification', 'identify', 'image_url', 'list', 'message_count', 'messages', 'muted', 'nickname', 'post', 'user_id'
# (Member messages are probably direct messages.)
#

import groupy
import logging
import argparse
import sys
import datetime

if __name__ == '__main__':
	# Take care of command line arguments
	parser = argparse.ArgumentParser(description='A script to identify GroupMe group members')
	
	# http://stackoverflow.com/questions/14097061/easier-way-to-enable-verbose-logging
	argGroup = parser.add_mutually_exclusive_group()
	argGroup.add_argument("-d", "--debug",help="Show very detailed logging",action="store_true" )
	argGroup.add_argument("-q", "--quiet",help="Show very little logging",action="store_true" )
	# If absent, just print a list of available groups and IDs
	parser.add_argument("groupID",help="Internal GroupMe Group ID you want to check",type=int,nargs='?')
	args = parser.parse_args()
	
	if args.debug:
		logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
	if args.quiet:
		logging.basicConfig(level=logging.ERROR, stream=sys.stderr)
	else:
		logging.basicConfig(level=logging.INFO, stream=sys.stderr)

		
	logging.debug("Loading list of GroupMe groups...")
	myGroups = groupy.Group.list()
	logging.debug("GroupMe groups loaded")
	
	# If we didn't specify a group, provide some info to help find the one we want
	if args.groupID is None:
		print("Groups you can see:")
		print("Group Name: Group ID")
		for group in myGroups:
			print("%s: %s" % (group.name,group.id))
	
	# We know the group we want, so we don't need to index all of them.
	found = False;
	logging.debug("Searching groups for ID %s" % (args.groupID))
	for group in myGroups:
		logging.debug("  Checking %s versus %s" % (group.id,args.groupID))
		if str(group.id) == str(args.groupID):
			logging.debug("Found group ID %s named %s" % (group.id,group.name))
			found = True;
			break
	
	if not found:
		raise NameError('Group ID not found in your list of visible groups')
		
	# The global members list is only people I've "seen", not the members of every
	# group I'm in. This loads the members of "group" explicitly
	members = group.members()

	print("\"GroupMe ID\",\"GroupMe Nickname\"")
	for member in members:
		logging.debug("Indexing member ID %s (%s)" % ( member.id, member.nickname))
		print("\"%s\",\"%s\"" % ( member.id, member.nickname) )
	
