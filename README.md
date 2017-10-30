# groupme-inactive-users
Script for finding inactive users in a given GroupMe group

Run without any arguments to list all the groups the API key can see, along with their group ID. This helps make it easier to pick the GroupID that will need to be passed to the script.

Sample usage:

    python groupme-inactive-users.py -d $GROUPID > $GROUPID-users.csv

The output is one line per user with their display name and the number of days since we last saw any activity for that user. Note that people with no activity and people with activity over the time limit are indistinguishable.

# groupme-members
Lists the member IDs and nicknames for every member of the given GroupMe group
