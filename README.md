# tiling-layout

**tiling-layout** is a QtLayout that allows to split widgets in a vim-like fashion.

![alt logo](https://raw.githubusercontent.com/lufte/tilinglayout/master/demo.gif)

## Usage
**tiling-layout** is currently written in Python3 and depends on PyQt5.
You will be able to use it in a Qt application only if it's written in Python as well.
Currently there is no other form of distribution than the source files in this repository.

To use the layout simply import the `QTilingLayout` class and create an instance with the inital widget to be shown.

### Available methods:
* `hsplit` to split a widget horizontally.
* `vsplit` to split a widget vertically.
* `remove_widget` to remove a widget from the layout.
Refer to the source file for detailed documentation on each method.

## Contributing
I welcome all contributions, specially ideas on how to distribute this as a library (do I port it to C++? do I make a python package?).
