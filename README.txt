*************************************************************************************
*                      Maze Navigation using BCI2000 P3Speller                      *
*                                 EE Senior Design                                  *
*                                    Version 1.0                                    *
*                        Peter Mansour (phm2122@columbia.edu)                       *
*************************************************************************************

requires python 3

To Run Server:	python3 server.py <IPv4_HOST> <PORT>

To join game: python3 join_game.py <IPv4_HOST> <PORT> <color> <BCI2000_app_log_path>

***Note there is a considerable latency between BCI2000 prediction of direction
and updating of players' position on screen. the simulations run much faster than 
P3Speller should in real-life