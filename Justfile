install: 
    echo 'PYTHONPATH="$PYTHONPATH:'"$(realpath .)"'" python3 -m ssg $@' > ~/.local/bin/ssg
    chmod +x ~/.local/bin/ssg
