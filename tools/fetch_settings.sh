
if ! command -v mongodump &> /dev/null
then
    echo "mongodump could not be found, please install it or ask to your system administrator!"
    exit
fi

if ! command -v mongorestore &> /dev/null
then
    echo "mongorestore could not be found, please install it or ask to your system administrator!"
    exit
fi

# demande à l'utilisateur si il veut les settings de wizz ou fixstudio
echo "Which settings do you want to fetch?"
echo "1) wizz"
echo "2) fixstudio"
read -p "Enter your choice: (1 or 2)
" choice

# si l'utilisateur veut les settings de wizz alors la variable host prend la valeur mongodb si l'utilisateur veut les settings de fixstudio alors la variable host prend la valeur dockerquad
if [ $choice -eq 1 ]
then
    HOST="openpype-mongo"
    PORT=27017
elif [ $choice -eq 2 ]
then
    HOST="dockerquad"
    PORT=27027
else
    echo "Invalid choice!"
    exit 1
fi
echo $HOST

# dump mongodb on remote server and restore it locally
mongodump --host=$HOST --port=$PORT --db=openpype --collection=settings --archive | mongorestore --host="localhost" --port=27017 --archive

exit 0
