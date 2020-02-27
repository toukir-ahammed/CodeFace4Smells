#! /usr/bin/env Rscript
# -*- R -*-
## This file is part of Codeface. Codeface is free software: you can
## redistribute it and/or modify it under the terms of the GNU General Public
## License as published by the Free Software Foundation, version 2.
##
## This program is distributed in the hope that it will be useful, but WITHOUT
## ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
## FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
## details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
##
## Copyright 2013 by Siemens AG, Wolfgang Mauerer <wolfgang.mauerer@siemens.com>
## All Rights Reserved.
## A script to download all messages posted on a gmane-archived mailing
## list starting with a specific date

s <- suppressPackageStartupMessages
s(library(RCurl))
s(library(lubridate))
s(library(stringr))
s(library(optparse))
rm(s)

download.mbox <- function(ml, num, outfile) {

  ## Execute the command to fetch the messages into an mbox file in
  ## the current directory. Note that this can require a considerable amount
  ## of time.
  ## TODO: Use nntp-pull --verbose, count the number of emitted
  ## lines, and provide a status progress bar.
  cmd <- str_c("nntp-pull --server=news.gmane.io --verbose --reget --limit=",
               num, " '", ml, ">", outfile, "' 2>&1")
  cat(str_c("Downloading ", num, " messages from ", ml, "\n"))
  cat(cmd, "\n")
  system(cmd)
  cat("Download completed.\n")
}

#####################################################################
parser <- OptionParser(usage = "%prog <ml> <num> <mbox>")
arguments <- parse_args(parser, positional_arguments = TRUE)
opts <- arguments$options

if (length(arguments$args) != 3) {
  print_help(parser)

  cat("Mandatory positional arguments:\n")
  cat("   <ml>: gmane name of the mailing list\n")
  cat("   <num>: Number of messages to download\n")
  cat("   <mbox>: mbox file name (is augmented with the suffix .mbox)\n")
  stop()
} else {
  ml <- arguments$args[1]
  num <- arguments$args[2]

  if (substr(arguments$args[3], nchar(arguments$args[3])-4, nchar(arguments$args[3])) == ".mbox") {
    outfile <- arguments$args[3]
  } else {
    outfile <- str_c(arguments$args[3], ".mbox")
  }
}

download.mbox(ml, num, outfile)


########################### Debugging ##############################
#download.mbox("gmane.comp.emulators.qemu", start.date)

## For the curious (we could re-use this graph instead of generating
## the data on our own from the message data)
#ggplot(dat, aes(x=date, y=posts)) + geom_line()
#ggplot(dat, aes(x=date, y=cumulative)) + geom_line()
