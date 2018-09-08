
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

file="$1"

echo "$file"
du -h "$file"
echo listing . files
find "$file" -name ".*"

echo "Name:"
read name
echo "Authors:"
read authors

python3 $DIR/upload.py "$(cat $DIR/key)" "$file" "$name" "$authors" "@article{,title={$name}}" dataset "" ""
