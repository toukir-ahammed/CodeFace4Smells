# Plot temporally resolved overview graphs for all project communities

# This file is part of Codeface. Codeface is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Copyright 2015 by Wolfgang Mauerer <wm@linux-kernel.net>
# All Rights Reserved.

library(igraph)
library(stringr)
source("interactive.r")
source("../clusters.r", chdir=TRUE)
source("../utils.r", chdir=TRUE)

## Adapt these as desired
conf <- create.conf("/vagrant/codeface.conf", "/vagrant/conf/qemu.conf")
output.dir <- "/tmp/qemu"

## Nothing configurable below here
plot.cluster <- function(g, ...) {
  V(g)$name <- NA
  V(g)$color <- "blue"
  E(g)$arrow.size=0.75
  E(g)$width <- E(g)$width*3

  plot(g, ...)
}

gen.ids.plot <- function(id, output.dir) {
    clusters.list <- prepare.clusters(conf$con, conf$pid, id, 99)

    output.dir <- str_c(output.dir, "/", id, "/")
    gen.dir(output.dir)

    null <- sapply(1:length(clusters.list), function(i) {
        pdf(str_c(output.dir, "/cluster_", i, ".pdf"))
        plot.cluster(clusters.list[[i]], layout=layout_with_dh, margin=0)
        dev.off()
    })
}

ids <- query.range.ids.con(conf$con, conf$pid)
null <- sapply(ids, function(id) { gen.ids.plot(id, output.dir) })
