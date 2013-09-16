#! /usr/bin/env Rscript

## This file is part of prosoda.  prosoda is free software: you can
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
## Copyright 2013 by Siemens AG, Johannes Ebke <johannes.ebke.ext@siemens.com>
## All Rights Reserved.

## This file should contain the overview widgets for the main dashboard
source("../symbols.r", chdir=TRUE)
source("../figures.of.merit.r", chdir=TRUE)

## Global status indicators for the project processing overview widget:
symbols.processing.status <- symbols.weather

## Global status indicators for the project status widget:
symbols.project.status <- symbols.emotion

## Status codes as factors from one of good, warn, bad, error
## factors obtained with as.status obey good > warn > bad > error
status.codes <- c("error", "bad", "mostly.bad", "warn", "mostly.good", "good")
status.codes.colors <- c(color.bad, color.bad, color.bad, color.warn, color.good, color.good)

as.status <- function(x) { factor(x, levels=status.codes, ordered=TRUE) }
status.good <- as.status("good")
status.mostly.good <- as.status("mostly.good")
status.warn <- as.status("warn")
status.mostly.bad <- as.status("mostly.bad")
status.bad <- as.status("bad")
status.error <- as.status("error")

as.color <- function(status) {
  status.codes.colors[[which(status.codes == status)]]
}

good.warn.bad.if <- function(x, good.limit, warn.limit) {
  if (x > good.limit) {
    status.good
  } else if (x > warn.limit) {
    status.warn
  } else {
    status.bad
  }
}

## Provide a round status indicator with the given background color
## and containing the specified symbol.
make.indicator <- function(symbol, color) {
  div(style=paste("margin: auto; ", "width: 50px; ", "height: 50px;",
                  " -webkit-border-radius: 25px;",
                  "-moz-border-radius: 25px;",
                  "border-radius: 25px;",
                  #"border-width:0.1px; border-style:solid; border-color:black;",
                  "box-shadow: 2px 2px 2.5px rgb(0,0,0);",
                  "line-height: 50px; text-align: center; vertical-align: middle;",
                  "font-size: 25px;",
                  "background-color:", color, ";"),
                  symbol)
}


## Return HTML for an overview box
overview.html <- function(title, bigtext, subtitle, link, subtitle.size="100%") {
  tagList(
    tags$div(class="grid_title", style="margin-top: 10px; margin-bottom: 20px;", title),
    tags$div(class='grid_bigtext', style="font-size:110px; text-align: center", bigtext),
    tags$p(style=paste("font-size:", subtitle.size, "; text-align: center; line-height: 40px; margin-top: 20px"), subtitle),
    p(a(href=link, "details..."))
  )
}

## Superclass constructor which already fills important variables
initWidget.widget.overview <- function(w) {
  # Call superclass
  w <- NextMethod(w)
  w$project.name <- reactive({query.project.name(conf$con, w$pid())})
  w$cycles <- reactive({get.cycles.con(conf$con, w$pid())})
  w$data <- reactive({
    pid <- w$pid()
    cycles <- w$cycles()
    list(
      n.commits = dbGetQuery(conf$con, str_c("SELECT COUNT(*) FROM commit WHERE projectId=", pid))[[1]],
      n.persons = dbGetQuery(conf$con, str_c("SELECT COUNT(*) FROM person WHERE projectId=", pid))[[1]],
      n.tsplots = dbGetQuery(conf$con, str_c("SELECT COUNT(*) FROM plots WHERE name LIKE 'Progress%' AND projectId=", pid))[[1]],
      n.issues = dbGetQuery(conf$con, str_c("SELECT COUNT(*) FROM issue WHERE projectId=", pid))[[1]],
      n.mail.threads = dbGetQuery(conf$con, str_c("SELECT COUNT(*) FROM mail_thread WHERE projectId=", pid))[[1]],
      n.understand.plots = dbGetQuery(conf$con, str_c("SELECT COUNT(*) FROM plots WHERE name LIKE 'Understand%' AND projectId=", pid))[[1]]
    )
  })
  return(w)
}

## Superclass method that derives the widgets background color from
## the average status value
widgetColor.widget.overview <- function(w) {
  reactive({
    ## Collaboration indicator color
    combined.status <- status.codes[mean(c(unlist(w$status())))]
    as.color(combined.status)
    color.neutral
  })
}

## Widget which presents a processing overview for prosoda operators
createWidgetClass(
  c("widget.overview.processing", "widget.overview"),
  "Project Processing Status", "Short, one-widget project processing status",
  c("invisible"),
  1, 1,
  html=htmlOutput
)

initWidget.widget.overview.processing <- function(w) {
  # Call superclass
  w <- NextMethod(w)
  w$status <- reactive({
    list(
      commits = good.warn.bad.if(w$data()$n.commits, 100, 10),
      timeseries = if (w$data()$n.tsplots > 0) { status.good } else { status.bad },
      issues = good.warn.bad.if(w$data()$n.issues, 10, 0),
      ml = good.warn.bad.if(w$data()$n.mail.threads, 100, 10),
      complexity = good.warn.bad.if(w$data()$n.understand.plots, 1, 0)
    )
  })
  return(w)
}

renderWidget.widget.overview.processing <- function(w) {
  renderUI({
    ## Take minimum status as combined status
    combined.status <- status.codes[mean(c(unlist(w$status())))]
    indicator.summary <- symbols.processing.status[[which(names(symbols.processing.status) == combined.status)]]

    indicator.commits <- make.indicator(symbol.commit, as.color(w$status()$commits))
    indicator.timeseries <- make.indicator(symbol.timeseries, as.color(w$status()$timeseries))
    indicator.issues <- make.indicator(symbol.bug, as.color(w$status()$issues))
    indicator.ml <- make.indicator(symbol.email, as.color(w$status()$ml))
    indicator.complexity <- make.indicator(symbol.analysis, as.color(w$status()$complexity))

    link <- paste("?projectid=", w$pid(), sep="")
    overview.html(w$project.name(), indicator.summary,
              tags$table(width="100%", tags$tr(
                                 tags$td(indicator.commits),
                                 tags$td(indicator.timeseries),
                                 tags$td(indicator.issues),
                                 tags$td(indicator.ml),
                                 tags$td(indicator.complexity)
                                 )),
              link
    )
  })
}

## Widget which creates an overview of a project for analysts
createWidgetClass(
  c("widget.overview.project", "widget.overview"),
  "Project Summary", "Short, one-widget project summary",
  NULL, # no topical restrictions
  1, 1,
  html=htmlOutput
)

initWidget.widget.overview.project <- function(w) {
  # Call superclass
  w <- NextMethod(w)
  w$status <- reactive({
    list(
      construction = good.warn.bad.if(w$data()$n.commits, 1000, 10),
      collab = good.warn.bad.if(w$data()$n.tsplots, 1, 0),
      comm = good.warn.bad.if(w$data()$n.mail.threads, 1000, 10),
      complex = good.warn.bad.if(w$data()$n.understand.plots, 10, 0)
    )
  })
  return(w)
}

renderWidget.widget.overview.project <- function(w) {
  renderUI({
    ## Collaboration indicator color
    combined.status <- status.codes[mean(c(unlist(w$status())))]
    indicator.summary <- symbols.processing.status[[which(names(symbols.processing.status) == combined.status)]]

    indicator.collaboration <- make.indicator(symbol.collaboration, as.color(w$status()$collab))
    indicator.construction <- make.indicator(symbol.construction, as.color(w$status()$construction))
    indicator.communication <- make.indicator(symbol.communication, as.color(w$status()$comm))
    indicator.complexity <- make.indicator(symbol.complexity, as.color(w$status()$complex))

    link <- paste("?projectid=", w$pid(), sep="")
    overview.html(w$project.name(), indicator.summary,
              tags$table(width="100%", tags$tr(
                                 tags$td(indicator.collaboration),
                                 tags$td(indicator.construction),
                                 tags$td(indicator.communication),
                                 tags$td(indicator.complexity)
                                 )),
              link
    )
  })
}

# weather, emotion, animals, abstract, gestures, arrows

createWidgetClass(
  c("widget.overview.communication", "widget.overview.topic"),
  "Communication", "Information on how developers communicate",
  c("overview", "communication"),
  1, 1,
  html=htmlOutput
)

createWidgetClass(
  c("widget.overview.collaboration", "widget.overview.topic"),
  "Collaboration", "Information on how developers communicate",
  c("overview", "collaboration"),
  1, 1,
  html=htmlOutput
)

createWidgetClass(
  c("widget.overview.complexity", "widget.overview.topic"),
  "Complexity", "Information on how developers communicate",
  c("overview", "complexity"),
  1, 1,
  html=htmlOutput
)

createWidgetClass(
  c("widget.overview.construction", "widget.overview.topic"),
  "Construction", "Information on the construction and architecture of the project",
  c("overview", "construction"),
  1, 1,
  html=htmlOutput
)

initWidget.widget.overview.communication <- function(w) {
  # Call superclass
  w <- NextMethod(w)
  w$figure.of.merit <- reactive({ figure.of.merit.communication(w$pid()) })
  w$symbol <- symbol.communication
  w$symbols <- symbols.emotion
  w$link <- reactive({ paste("?topic=communication&projectid=", w$pid(), sep="") })
  w$status <- reactive({ good.warn.bad.if(w$figure.of.merit(), .5, .9) })
  return(w)
}

initWidget.widget.overview.collaboration <- function(w) {
  # Call superclass
  w <- NextMethod(w)
  w$figure.of.merit <- reactive({ figure.of.merit.collaboration(w$pid()) })
  w$symbol <- symbol.collaboration
  w$symbols <- symbols.gestures
  w$link <- reactive({ paste("?topic=collaboration&projectid=", w$pid(), sep="") })
  w$status <- reactive({ good.warn.bad.if(w$figure.of.merit(), .5, .9) })
  return(w)
}

initWidget.widget.overview.construction <- function(w) {
  # Call superclass
  w <- NextMethod(w)
  w$figure.of.merit <- reactive({ figure.of.merit.construction(w$pid()) })
  w$symbol <- symbol.construction
  w$symbols <- symbols.abstract
  w$link <- reactive({ paste("?topic=construction&projectid=", w$pid(), sep="") })
  w$status <- reactive({ good.warn.bad.if(w$figure.of.merit(), .5, .9) })
  return(w)
}

initWidget.widget.overview.complexity <- function(w) {
  # Call superclass
  w <- NextMethod(w)
  w$figure.of.merit <- reactive({ figure.of.merit.complexity(w$pid()) })
  w$symbol <- symbol.complexity
  w$symbols <- symbols.arrows
  w$link <- reactive({ paste("?topic=complexity&projectid=", w$pid(), sep="") })
  w$status <- reactive({ good.warn.bad.if(w$figure.of.merit(), .5, .9) })
  return(w)
}

renderWidget.widget.overview.topic <- function(w) {
  #reactive({list(text=intToUtf8(0x2197), subtext="++")})
  renderUI({
    status.symbol <- w$symbols[[which(names(w$symbols) == w$status())]]
    overview.html(w$name, status.symbol, w$symbol, w$link(), "400%")
  })
}

widgetColor.widget.overview.topic <- function(w) {
  reactive({
    ## Collaboration indicator color
    combined.status <- status.codes[w$status()]
    as.color(combined.status)
  })
}
#renderWidget.widget.overview.construction <- renderWidget.widget.overview.communication
#renderWidget.widget.overview.collaboration <- renderWidget.widget.overview.communication
#renderWidget.widget.overview.complexity <- renderWidget.widget.overview.communication
