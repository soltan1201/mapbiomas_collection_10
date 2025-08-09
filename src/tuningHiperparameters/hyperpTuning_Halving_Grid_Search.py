import os
import sys
import json
import glob
import argparse
import pandas as pd
from tabulate import tabulate
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn import ensemble
from sklearn.pipeline import Pipeline
import seaborn as sns
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import train_test_split
# explicitly require this experimental feature
from sklearn.experimental import enable_halving_search_cv
# now you can import normally from model_selection
from sklearn.model_selection import HalvingGridSearchCV
from sklearn.model_selection import HalvingRandomSearchCV
import multiprocessing

from pathlib import Path
pathparent = str(Path(os.getcwd()).parents[0])
print("pathparent ", pathparent)


# https://inria.github.io/scikit-learn-mooc/python_scripts/parameter_tuning_grid_search.html
# 3.2.3. Searching for optimal parameters with successive halving
# HalvingGridSearchCV 
# https://scikit-learn.org/stable/modules/grid_search.html
pathROIs = "/home/superusuario/Dados/mapbiomas/col8/features/ROIsCSV/ROIsV5Col8man/"
# path_folder = '/home/superuser/Dados/mapbiomas/dev_mapping_soil_colection_beta/src/dados/patchs'
parser = argparse.ArgumentParser()
parser.add_argument('names_folders', type=str,  
                    default= pathROIs, 
                    help="set the dir of folders to read ROIs csv" 
            )
try:
    args = parser.parse_args()
    tmpFolder = args.names_folders
    if str(pathROIs) != str(tmpFolder):
        print("<<<<<< change the path folder  >>>>>>>>>>>>>> ")
        pathROIs = tmpFolder
        print("loading from >> ", pathROIs)
except argparse.ArgumentTypeError as e:
    print(f"Invalid argument: {e}")

a_file = open( "dict_lst_features_by_basin.json", "r")
dictFeatureImp = json.load(a_file)
# print("  ", dictFeatureImp)


# @retry(tries=10, delay=1, backoff=2)
def processingROIs_gridSearch(cont, path_name):
    # featFirst = listCSVsRoi[0]
    name_file = path_name.split("/")[-1]
    print("processing features ", name_file)
    idBasin = name_file.replace(".csv", "")
    df_rois = pd.read_csv(path_name)
    lst_col = [kk for kk in df_rois.columns]
    lst_col.remove('system:index')
    lst_col.remove('.geo')
    lst_col.remove('class')
    # print("lista de coluna \n ==> ", lst_col)
    print("número de colunas ", len(lst_col))
    print(df_rois.shape)
    lstFeatSelect = [ncol for ncol in lst_col if ncol in dictFeatureImp[idBasin]]
    print("  featureSelection \n ", lstFeatSelect)
    number_samples = [10, 20, 35, 40, 45, 60, 65, 70, 80, 160]
    # sys.exit()
    for yyear in range(1985, 2023):
        dfYY = df_rois[df_rois['year'] == yyear]# [lstFeatSelect + ['class']]
        print(f"now we process with shape table {dfYY.shape}")
        data_train, data_test, target_train, target_test = train_test_split(
                                                                dfYY[lstFeatSelect], dfYY["class"], 
                                                                test_size=0.2, random_state=42
                                                            )
        # 'numberOfTrees': 72, 
        # 'shrinkage': 0.005, 
        # 'samplingRate': 0.8, 
        # 'loss': 'Huber',#'LeastAbsoluteDeviation', 
        # 'seed': 0
        model = Pipeline([            
                    ("classifier", ensemble.GradientBoostingClassifier(
                                        random_state=42, 
                                        max_leaf_nodes=4
                                    ))
                ])
        print("Modelo Pipelaine ", model)

        param_grid = {
            'classifier__learning_rate': (0.01, 0.1, 1, 5, 10),
            'classifier__max_leaf_nodes': (3, 10, 30, 50)
        }
        model_grid_search = GridSearchCV(
                                    model, 
                                    param_grid= param_grid,
                                    n_jobs=2, 
                                    cv=2
                                )
        model_grid_search.fit(data_train, target_train)
        accuracy = model_grid_search.score(data_test, target_test)
        print(
            f"The test accuracy score of the grid-searched pipeline is: {accuracy:.2f}")

        model_grid_search.predict(data_test)

        print(f"The best set of parameters is: "
            f"{model_grid_search.best_params_}")

        cv_results = pd.DataFrame(model_grid_search.cv_results_).sort_values(
            "mean_test_score", ascending=False)
        # print(cv_results.head(6))
        print(tabulate(cv_results.head(6), headers = 'keys', tablefmt = 'psql'))
        #dados/Hyperparameter/
        path_outputCSV = os.path.join(pathparent, "dados/Hyperparameter")
        cv_results.to_csv(os.path.join(path_outputCSV, f"{idBasin}_{yyear}.csv"))

        # get the parameter names
        # column_results = [f"param_{name}" for name in param_grid.keys()]
        # column_results += [
        #     "mean_test_score", "std_test_score", "rank_test_score"]
        # cv_results = cv_results[column_results]

        # def shorten_param(param_name):
        #     if "__" in param_name:
        #         return param_name.rsplit("__", 1)[1]
        #     return param_name


        # cv_results = cv_results.rename(shorten_param, axis=1)
        # print("CV_resultado ", cv_results)

        # pivoted_cv_results = cv_results.pivot_table(
        #     values="mean_test_score", index=["learning_rate"],
        #     columns=["max_leaf_nodes"])

    # print(pivoted_cv_results)

    # ax = sns.heatmap(pivoted_cv_results, annot=True, cmap="YlGnBu", vmin=0.7,
    #                 vmax=0.9)
    # ax.invert_yaxis()


# listCSVsRoi = glob.glob(pathROIs + "/*csv")
listCSVsRoi = os.listdir(pathROIs)
print(pathROIs)
print("lista de ROIs em CSV >>> ", listCSVsRoi)
for cc, nfile in enumerate(listCSVsRoi[:]):
    print(f" #{cc} processing >> {os.path.join(pathROIs, nfile)}")
    processingROIs_gridSearch(cc, os.path.join(pathROIs, nfile))