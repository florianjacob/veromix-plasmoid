#!/bin/bash
ps -ef | grep  VeromixService  | grep -v grep | awk '{print $2}' | xargs kill -s TERM  

