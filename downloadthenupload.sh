
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

#echo "URL:"
#read url
url=$1
echo "Name:"
read name
echo "Authors:"
read authors


wget -c "$url"
python3 $DIR/upload.py "$(cat $DIR/key)" "${url##*/}" "$name" "$authors" "@article{}" dataset "" "$url"
