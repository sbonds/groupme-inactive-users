#!/usr/bin/env python

# Usage:
#  groupme-inactive-users.py <group number> > <group number>-inactive-users.csv
# Find a list of people who appear to be inactive in a Groupme group
# Possible filtering options
# + show everyone who has not been active since a particular date
# + show everyone who has not been active for a particular number of days before the current date
# + show the 'n' least active people
# + show the least active 'n'% of the group's membership
#
# Which would be simplest for the first implementation yet still useful?
# + show everyone who has not been active for a particular number of days before the current date
#
# Info needed:
# + API authentication token (OAuth requires a callback URL, and this isn't a web app so the token must be pulled from an active session.)
# + Group ID (also pulled from an active session)
# + days back to search for activity
#
# Method:
# + Retrieve member list of group: https://dev.groupme.com/docs/v3#groups_show
# ++ for user name to user id mapping
# ++ also shows group creator, which could be useful if a group needs to be enlarged
# + Retrieve messages: https://dev.groupme.com/docs/v3#messages
# ++ Loop until systime of processed message is older than "days back to search":
# ++ is a before_id set?
# +++ No: Get most recent batch of 100: JSON {"limit": 100}
# +++ Yes: Get the batch of 100 before before_id
# +++ Loop over batch of 100 messages to process:
# ++++ Record oldest message ID
# ++++ Note message system time: older than "days back to search"? Yes: break out of outer loop; No: keep going
# ++++ Record "most recent interaction" system times for each ID found (e.g. a message posted or a messaged favorited by using the system time of the message)

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
# Handy helper function
# message.likes() is a list of member objects who have liked a message. Nice!

import groupy
import logging
import argparse
import sys
import datetime

if __name__ == '__main__':
	# Take care of command line arguments
	parser = argparse.ArgumentParser(description='A script to identify idle GroupMe group members')
	
	# http://stackoverflow.com/questions/14097061/easier-way-to-enable-verbose-logging
	argGroup = parser.add_mutually_exclusive_group()
	argGroup.add_argument("-d", "--debug",help="Show very detailed logging",action="store_true" )
	argGroup.add_argument("-q", "--quiet",help="Show very little logging",action="store_true" )
	parser.add_argument("-D", "--days",help="Days to go back checking for activity",type=int,default=365)
	# If absent, just print a list of available groups and IDs
	parser.add_argument("groupID",help="Internal GroupMe Group ID you want to check",type=int,nargs='?')
	args = parser.parse_args()
	
	if args.debug:
		logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
	if args.quiet:
		logging.basicConfig(level=logging.ERROR, stream=sys.stderr)
	else:
		logging.basicConfig(level=logging.INFO, stream=sys.stderr)

	daysAgo = datetime.datetime.now() - datetime.timedelta(days=args.days)
	logging.info("Will check for messages newer than %s (%s days ago)" % (daysAgo,args.days))
		
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
	
	memberById = {}
	memberByNickname = {}
	for member in members:
		logging.debug("Indexing member ID %s (%s)" % ( member.id, member.nickname))
		# PROBLEM: the member.id doesn't seem to match the message.user_id number even when the nicknames match
		memberById[member.id] = member
		# Nicknames seem to match the name in the message.name field
		memberByNickname[member.nickname] = member
	
	logging.info("Done indexing all known GroupMe members. Checking old messages from your chosen group.")
	
	# Load messages into a list until we hit the date desired. Memory is cheap, right?
	messages=group.messages()
	while messages.oldest.created_at > daysAgo:
		logging.info("%s messages loaded, oldest dated %s" % (len(messages), messages.oldest.created_at))
		try:
			messages.iolder()
		except TypeError:
			logging.warning("messages.iolder() had a problem (%s), trying to proceed anyhow." % (sys.exc_info()[0]))
			break
		
		# Getting this when GroupMe returns a 304. Seems to be that the "e" ApiError object
		# isn't a dictionary so ['code'] doesn't work on it.
		# File "/home/groupme/lib/python3.5/site-packages/groupy/object/responses.py", line 129, in messages
		#     if e.args[0]['code'] == status.NOT_MODIFIED:
		# TypeError: 'Response' object is not subscriptable
		# Contacted the package author Mar 16 2016 to report the bug
		#  https://github.com/rhgrant10/Groupy/issues/20
		
	logging.debug("Final: %s messages loaded, oldest dated %s" % (len(messages),messages.oldest.created_at))
	
	# Make a dictionary of datetime entries of the most recent activity for each user indexed by nickname
	latestActivity = {}
	
	for message in messages:
		logging.debug("Analyzing message: UID %s name: %s date: %s" % (message.user_id, message.name, message.created_at))
		if latestActivity.get(message.name,datetime.datetime.min) < message.created_at:
			# This is newer than our previous activity
			logging.debug("Found more recent activity for user '%s': updating time" % ( message.name) )
			latestActivity[message.name] = message.created_at
			
		for memberWhoLikesThis in message.likes():
			if latestActivity.get(memberWhoLikesThis.nickname,datetime.datetime.min) < message.created_at:
				logging.debug("Found more recent activity for user %s (liked a message): updating time" % ( memberWhoLikesThis) )
				latestActivity[memberWhoLikesThis.nickname] = message.created_at
				
	print("Group: %s" % (group.name))
	print("NickName,Last Activity Days Ago")
	now = datetime.datetime.now()
	for userNickname in memberByNickname:
		try:
			timeSince = now - latestActivity[userNickname]
			days = timeSince.days
		except KeyError:
			days = ">" + str(args.days)
			
		print("\"%s\",\"%s\"" % ( userNickname, days))