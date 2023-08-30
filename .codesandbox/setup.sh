WORKSPACE="/workspace"

# Install python dependencies
poetry update && poetry install

cd $WORKSPACE

# Install whichpy
WHICHPY="https://gist.githubusercontent.com/pwwang/879966128b0408c2459eb0a0b413fa69/raw/e3c49ba0a6b6794ef8a3b9039134cd0e869c55a8/whichpy.fish"
curl -sS $WHICHPY > ~/.config/fish/functions/whichpy.fish
