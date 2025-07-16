
library("DESeq2")

argument = commandArgs(trailingOnly =TRUE)

read_count_table = argument[1]
exp_condition_table = argument[2]

reference_condition = argument[3]
second_condition = argument[4]
output_file = argument[5]

#The gene name column should have header "Probe"
#The format should be CSV with delimiter ","
#cts file to pass via argv
cts <- as.matrix(read.csv(read_count_table,row.names=1, check.names=FALSE))

#colData file to pass via argv
colData <- read.csv(exp_condition_table,sep="\t",row.names = 1, check.names=FALSE)
colData$Conditions <- factor(colData$Conditions)

#Create the dds object
dds <- DESeqDataSetFromMatrix(countData = cts, colData = colData, design = ~ Conditions)
dds$Conditions <- relevel(dds$Conditions, ref = reference_condition)

#Calculate the DEG
dds <- DESeq(dds)
res <- results(dds, contrast=c("Conditions",reference_condition,second_condition))


write.csv(as.data.frame(res), file=output_file)




#tempoportal_r_env

#Rscript DGE_deseq2.r for_gio_2_count_table.csv condition_table.tsv control treatment out
