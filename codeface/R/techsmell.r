#! /usr/bin/env Rscript

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

source("config.r")
source("query.r")

set.seed(432)

##################### tech smell analysis #########################

## Main tech smell analysis function
techsmell.analysis <- function (techsmelldir, gitdir, conf) {

    release_range.ids = get.cycles(conf)[, c("range.id")]
    for (range_id in release_range.ids) {
        file.to.import <- file.path(techsmelldir, paste("release_", range_id, ".csv", sep=""))
        if (file.exists(file.to.import)) {
            csv <- read.csv(file=file.to.import, header=TRUE)
            csv$classDataShouldBePrivate <- as.numeric(csv$classDataShouldBePrivate == "true")
            csv$complexClass <- as.numeric(csv$complexClass == "true")
            csv$functionalDecomposition <- as.numeric(csv$functionalDecomposition == "true")
            csv$godClass <- as.numeric(csv$godClass == "true")
            csv$spaghettiCode <- as.numeric(csv$spaghettiCode == "true")
            csv$hasLongMethods <- as.numeric(csv$hasLongMethods == "true")
            new.data <- data.frame("range.id"=range_id, csv)
            final.data <- data.frame(lapply(new.data, function(x) { gsub(gitdir, "", x, fixed=TRUE) }))
            write.techsmell.db(final.data, conf)
        }
    }
    write.tech.and.community.smell.db(release_range.ids, conf)
    data.to.export <- get.tech.and.community.smell.db(release_range.ids, conf)
    write.csv(data.to.export, file=file.path(techsmelldir, "report.csv"), row.names=FALSE)
}

######################### Dispatcher ###################################
config.script.run({
  conf <- config.from.args(positional.args=list("resdir"), require.project=TRUE)
  techsmelldir <- file.path(conf$resdir)
  gitdir <- file.path(conf$repo)
  
  ## run analysis
  techsmell.analysis(techsmelldir, gitdir, conf)
})