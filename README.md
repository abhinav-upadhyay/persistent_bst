This is just a PoC to explore how to create a disk backed data structure and manipulate it

It implements a bare bones BST with an integer type key and string type values, and backs them
to a file. The index is maintained in a file called `index.txt`, while the data lives in a file
called `data.txt`

## Usage:
This can be run as a REPL via
```shell
python bst.py
```

In the REPL, the follwing commands are supported:
### put (put a key-value)
`put <integer key> <value>`

For example

`put 10 apple`
`put 30 maple`

### get (get a key-value)

`get <integer key>`

For example

```
get 10
>> apple
```

```
get 50
>> None
```

### get * (gets all key-values)

This will print all the keys and their values stored in the index
