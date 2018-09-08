
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo DIR $DIR

url=$1

echo "Folder Name"
read foldername
echo "Name:"
read name
echo "Authors:"
read authors

mkdir $foldername
cd $foldername
youtube-dl $url
cd ..



python3 $DIR/upload.py "$(cat $DIR/key)" "$foldername" "$name" "$authors" "@article{,title={$name}}" dataset "" "$url"
