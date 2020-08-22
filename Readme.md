# NFS Most Wanted AI

## See this AI in practice

**todo**


## Descripton

A simple AI for NFS most wanted using realtime image processing. The detects the road ahead and the car's current speed. Using some heuristics based on this information, the AI simulates keyboard input to drive the car during a race.

The car was only finetuned up to 230 km/h. Feel free to finetune it further.


## Dependencies
Python 3.8

```
pip install -r requirements.txt
```

## Usage

The process must run as a background service while the game is running. The game must be either run in a virtual machine or in windowed mode, otherwise it will ignore our key inputs. For running it in windowed mode, i recommend using https://github.com/ThirteenAG/WidescreenFixesPack .

**Some heuristics and timings might differ depending on your machine. The code was tweaked to run on a 3.5GHz I5-7600 (no GPU acceleration)**
(too much/little computing time between frames might affect the AI's decisions and timings).

```
python main.py
```

Also save videos in ./out (needed this for the youtube video) :

```
mkdir out && python main.py save
```
