/*
 * evaluator.cpp
 *   created on: April 24, 2013
 * last updated: May 10, 2020
 *       author: Shujia Liu
 *
 * Modified by Okan Arslan for the Amazon Routing Challenge on Jun 8, 2021. 
 *
 */

#ifndef __EVALUATOR__
#include "evaluator.h"
#endif
#include <math.h>
#include <iostream>
using namespace std;

TEvaluator::TEvaluator() {
	Ncity = 0;
	fNearNumMax = 50;
}

TEvaluator::~TEvaluator() {}

void TEvaluator::setInstance(const string& filename) {
	FILE* fp;
	int n;
	char word[ 8000 ], type[ 80 ];
	fp = fopen(filename.c_str(), "r");
	while( 1 ){
		if( fscanf( fp, "%s", word ) == EOF ) break;
		if( strcmp( word, "DIMENSION" ) == 0 ){
			fscanf( fp, "%s", word );
			fscanf( fp, "%d", &Ncity );
		}
		if( strcmp( word, "EDGE_WEIGHT_TYPE" ) == 0 ){
			fscanf( fp, "%s", word );
			fscanf( fp, "%s", type );
		}
		if( strcmp( word, "NODE_COORD_SECTION" ) == 0 ) break;
		if( strcmp( word, "EDGE_WEIGHT_SECTION" ) == 0 ) break;
	}

	x.resize(Ncity);
	y.resize(Ncity);
	vector<int> checkedN(Ncity);

	fEdgeDis.clear();
	for (int i = 0; i < Ncity; i++) {
		vector<int> row(Ncity);
		fEdgeDis.push_back(row);
	}	

	fNearCity.clear();
	for (int i = 0; i < Ncity; i++) {
		vector<int> row(fNearNumMax + 1);
		fNearCity.push_back(row);
	}

	if( strcmp( type, "EXPLICIT" ) == 0  ) {
		for( int i = 0; i < Ncity; ++i ){
			for( int j = 0; j < Ncity; ++j ){
				fscanf( fp, "%s", word );
				fEdgeDis[ i ][ j ]=(int)atof( word );
			}
		}	
	} else {
		printf( "EDGE_WEIGHT_TYPE is not supported\n" );
		exit( 1 );
	}
	
	fclose(fp);

	
	int ci, j1, j2, j3;
	int cityNum = 0;
	int minDis;
	for( ci = 0; ci < Ncity; ++ci ){
		for( j3 = 0; j3 < Ncity; ++j3 ) checkedN[ j3 ] = 0;
		checkedN[ ci ] = 1;
		fNearCity[ ci ][ 0 ] = ci;
		for( j1 = 1; j1 <= fNearNumMax; ++j1 ) {
			minDis = 100000000;
			for( j2 = 0; j2 < Ncity; ++j2 ){
				if( fEdgeDis[ ci ][ j2 ] <= minDis && checkedN[ j2 ] == 0 ){
					cityNum = j2;
					minDis = fEdgeDis[ ci ][ j2 ];
				}
			}
			fNearCity[ ci ][ j1 ] = cityNum;
			checkedN[ cityNum ] = 1;
		}
	}
}

void TEvaluator::doIt( TIndi& indi ) {
	int d = 0;
	for( int i = 0; i < Ncity; ++i ) d += fEdgeDis[ i ][ indi.fLink[i][0] ] + fEdgeDis[ i ][ indi.fLink[i][1] ];
	indi.fEvaluationValue = d/2;
}

void TEvaluator::writeTo( FILE* fp, TIndi& indi ){
	Array.resize(Ncity);
	int curr=0, st=0, count=0, pre=-1, next;
	while( 1 ){
		Array[ count++ ] = curr + 1;
		
		if( indi.fLink[ curr ][ 0 ] == pre ) next = indi.fLink[ curr ][ 1 ];
		else next = indi.fLink[ curr ][ 0 ];

		pre = curr;
		curr = next;
		if( curr == st ) break;
	}
	if( this->checkValid( Array, indi.fEvaluationValue ) == false )
		printf( "Individual is invalid \n" );
	//fprintf( fp, "%d %d\n", indi.fN, indi.fEvaluationValue );
	for( int i = 0; i < indi.fN; ++i )
		fprintf( fp, "%d ", Array[ i ] );
	//fprintf( fp, "\n" );
}

bool TEvaluator::checkValid(vector<int>& array, int value) {
	return true;
}

