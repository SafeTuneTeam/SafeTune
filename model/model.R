library(HieRanFor)

# Testing set software
software <- factor(c('postgresql', 'spark', 'squid'))

readData <- function(fileName, dim) {
  
  dataTest <- read.csv(fileName, header=F)
  Xt <- matrix(nrow=0, ncol=dim)
  
  # convert factor(vector) to text(vector), then to number(vector), then combine them to matrix.
  for (i in 1:nrow(dataTest)) {
    vec_str <- as.character(dataTest[i,][2][1,1])
    vec <- jsonlite::stream_in(textConnection(vec_str), simplifyDataFrame = FALSE)
    Xt <- rbind(Xt, vec)
  }
  
  # bind data to label and index.
  X <- cbind(data.frame(Xt), dataTest[,c('V3','V4')])
  X <- cbind(dataTest[,1], X)
  
  return(X)
}

# the precision & recall will be shown here
outFile <- file("result.txt", "w")

# length of input vector
XdataDim <- 256

# training set (embedded)
X_train <- readData("SafeTuneTrain.csv", XdataDim)

for (s in software) {
  
  test_Path <- paste("SafeTuneTest_", s, ".csv", sep="")
  X_test <- readData(test_Path, XdataDim)
  
  lab_start <- ncol(X_train)-1
  lab_end <- ncol(X_train)
  
  hie.RF.SafeTune <- RunHRF(train.data        = X_train,
                            case.ID           = 1,
                            hie.levels        = c(lab_start:lab_end),
                            mtry              = "tuneRF2",
                            ntree             = 500,
                            internal.end.path = TRUE)
  
  
  perf.hRF.SafeTune <- PerformanceNewHRF(hie.RF = hie.RF.SafeTune,
                                       new.data = X_test,
                               new.data.case.ID = 1,
                                   new.data.hie = c(lab_start:lab_end),
                                     crisp.rule = c("multiplicative.permutation"),
                                      per.index = c("hie.F.measure"),
                                        by.node = TRUE)
  
  
  hie.performance.SafeTune <- perf.hRF.SafeTune$hie.performance

  effectiveness <- as.character(hie.performance.SafeTune[order(hie.performance.SafeTune$h.precision, decreasing=TRUE),][1,])

  # write precision, recall, F-score to the output file.
  write(s, outFile, append=T)
  write(names(effectiveness), outFile, append=T)
  write(as.character(effectiveness), outFile, append=T)
}

close(outFile)
