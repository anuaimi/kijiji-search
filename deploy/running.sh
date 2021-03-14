
# restart the container
docker start kijiji-search

# check the output
docker logs kijiji-search

# clear the log file of old runs
export LOG_FILE=`docker inspect --format='{{.LogPath}}' kijiji-search`
truncate -s 0 $LOG_FILE


# if want to check database
sudo apt install sqlite3
sqlite3 data/kijiji.db

# select * from listings
# .exit
