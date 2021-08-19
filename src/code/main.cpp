/*
 * main.cpp
 *   created on: April 24, 2013
 * last updated: May 10, 2020
 *       author: Shujia Liu
 *
 * Modified by Okan Arslan for the Amazon Routing Challenge on Jun 8, 2021. 
 */


#ifndef __ENVIRONMENT__
#include "environment.h"
#endif

#include <stdio.h>
#include <stdlib.h>
#include <iostream>
#include <vector>
#include <string>
using namespace std;

int main( int argc, char* argv[] ){

	
	char* filename = (char*)malloc(sizeof(char) * 800);	
	//strcpy(filename, "../temp/Route.tsp");
	
	if(argc > 1) 
		strcpy(filename, argv[1]);
	
	InitURandom(); 
	int maxNumOfTrial;

	TEnvironment* gEnv = new TEnvironment();
	gEnv->fFileNameTSP=(char*)malloc(200);

	//gEnv->maxTime=(char*)malloc(200);
	
	int id = 0;

	strcpy(gEnv->fFileNameTSP, filename);
	
	maxNumOfTrial = 1; // repeated times
	gEnv->Npop = 50; // number of items
	gEnv->Nch = 50; // number of offsprings

	gEnv->define();
	for (int n = 0; n < maxNumOfTrial; ++n){ 
		gEnv->doIt(); 
		//gEnv->printOn(n);
		gEnv->writeBest();
	}
	return 0;
}
