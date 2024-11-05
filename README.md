## About The Project
This repo implement a B+ tree with full redistribition, that is,
both insertion and deletion triggers redistribution if possible.

## Definition
Definition used in this project is stated as follows:
- Knuth Order (upper bound) ceil(k/2) <= # of node <= k
- Fill factor: 0.5
- Insertion overflow
  - rotate to left
  - failed
    - rotate to right
    - failed
      - split -> merge into parent
- Deletion underflow 
  - borrow from left sibling
  - failed
    - merge with left sibling
    - failed
      - borrow from right sibling
      - failed
        - merge with right sibling

## Getting Started

### Prerequisites
- Python 3.12+

### Installation
```
git clone https://github.com/dereklee0310/redistribute-b-plus-tree
```

## Usage
### Arguments
```
usage: main.py [-h] [-o ORDER] [-f FILE] [-s SEQUENTIAL [SEQUENTIAL ...]] [-b BULK_LOAD [BULK_LOAD ...]]

An interactive interface for B+ tree.

options:
  -h, --help            show this help message and exit
  -o ORDER, --order ORDER
                        order of the b+ tree, default to 4
  -f FILE, --file FILE  input file path
  -s SEQUENTIAL [SEQUENTIAL ...], --sequential SEQUENTIAL [SEQUENTIAL ...]
                        initialize B+ tree using sequential insertion
  -b BULK_LOAD [BULK_LOAD ...], --bulk-load BULK_LOAD [BULK_LOAD ...]
                        initialize B+ tree using bulk loading
```
### Commands
| Operation | Command       |
| --------- | ------------- |
| Insert    | `i <integer>` |
| Delete    | `d <integer>` |
| Display   | `D`           |
| Quit      | `q`           |

## Contact
Dereklee0310@gmail.com

## Acknowledgments
* Damon, lecturer of CCU DBMS 113
* https://github.com/solangii/b-plus-tree
* https://gist.github.com/savarin/69acd246302567395f65ad6b97ee503d
* https://www.youtube.com/watch?v=CYKRMz8yzVU
* https://www.youtube.com/watch?v=_nY8yR6iqx4