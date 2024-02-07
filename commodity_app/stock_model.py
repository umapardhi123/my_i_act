import pandas as pd
import numpy as np

from feature_engine.outliers import Winsorizer
from feature_engine.encoding import OneHotEncoder,OrdinalEncoder
from feature_engine.imputation import DropMissingData
from feature_engine.imputation import MeanMedianImputer,AddMissingIndicator,CategoricalImputer
from feature_engine.transformation import LogTransformer

from sklearn.model_selection import train_test_split

from sklearn.pipeline import Pipeline
import xgboost as xgb

# extras
import warnings
warnings.filterwarnings('ignore')
pd.set_option('display.max_columns', None)

df=pd.read_csv("commodity_app/merge.csv",parse_dates=['created_date'])
df = df.drop(columns=['Unnamed: 0', 'Unnamed: 0.1', 'splits', 'dividends'], axis=1)


# Parent class
class Test_handler():
    
  def cleanTest(self, df):  
    
#     df['Price'] = pd.to_numeric(df['Price'].replace({'$': '', 'nan': np.nan}), errors='coerce')

    # check if 'Price' column contains 'nan' or '$' values
    if 'nan' in df['Price'].values or '$' in df['Price'].values:
        # replace 'nan' values with NaN
        df['Price'] = df['Price'].replace('nan', np.nan)
        # remove the '$' sign from the 'Price' column and convert to float
        df['Price'] = df['Price'].str.replace('$', '').astype(float)
    
#     df['Price_Target'] =pd.to_numeric(df['Price_Target'].replace({'$': '', 'nan': np.nan}), errors='coerce')

    # check if 'Price_Target' column contains 'nan' or '$' values
    if 'nan' in df['Price_Target'].values or '$' in df['Price_Target'].values:
        # replace 'nan' values with NaN
        df['Price_Target'] = df['Price_Target'].replace('nan', np.nan)
        # remove the '$' sign from the 'Price' column and convert to float
        df['Price_Target'] = df['Price_Target'].str.replace('$', '').astype(float)
        
    # replace values in the 'Price_Target' column that contain 'k' with their numeric value in thousands
    if 'Price_Target' in df.columns and df['Price_Target'].dtype == 'object':
        df.loc[df['Price_Target'].str.contains('k', na=False, regex=True), 'Price_Target'] = df.loc[df['Price_Target'].str.contains('k', na=False, regex=True), 'Price_Target'].apply(lambda x: float(x.replace('k', '')) * 1000)

    df['Price_Target'] = df['Price_Target'].astype(float)
    
    return df



class ModelPipeline(Test_handler):
    
    def __init__(self):
      self.__AddMissingIndicatorVariables = ['Price','Price_Target']
      self.__MeanMedianImputerVarables = ['Price_Target']
      self.__WinsorizerCappingVarables = ['open', 'low', 'close', 'volume', 'high', 'adjclose', 'Price', 'Price_Target']
      self.__LogTransformerVarables = ['open', 'low', 'close', 'volume', 'high', 'adjclose', 'Price', 'Price_Target']
      self.__OneHotEncoderVariables = ['Ticker']
      

      self.pipe = Pipeline([
          
          #  Missing indicator
          ('Add missing indicator',AddMissingIndicator(
            variables=self.__AddMissingIndicatorVariables)),
    
          #   Median Missing Imputation
          ('Median Missing Imputation',MeanMedianImputer(
            imputation_method='median', variables=self.__MeanMedianImputerVarables)),

          #   Outlier Imputation
          ('Winsorizer_CAPPING',Winsorizer(
            capping_method='iqr', variables=self.__WinsorizerCappingVarables)),        

          # Feature Transformation
          ('LogTransformer',LogTransformer(
            variables=self.__LogTransformerVarables)),

          #  OneHotEncoder
          ('OneHotEncoder',OneHotEncoder(
            drop_last=True,variables=self.__OneHotEncoderVariables)),

          # Model Train
          ('Model', xgb.XGBClassifier(colsample_bytree=0.8, learning_rate=0.1, max_depth=5, n_estimators=200, subsample=0.8))
      ])
    
    def handleData(self, df):
        
        df = super().cleanTest(df)  # call parent class's cleanTest() method       
        df['created_date'] = pd.to_datetime(df['created_date'], format='%Y-%m-%d').astype('int64') // 10**9
        df['Ticker'] = np.where(df['Ticker'].map(df['Ticker'].value_counts()) >= 10, df['Ticker'], 'Other')
#         df = df.drop(columns=['Unnamed: 0', 'Unnamed: 0.1', 'splits', 'dividends'], axis=1).iloc[:, :]
        df['Consensus'] = df['Consensus'].apply(lambda x: np.where(x == 'none', np.nan, x))
        # df['Consensus'] = df['Consensus'].replace({'none': np.nan}).map({'Strong Buy': 0, 'Buy': 1, 'Hold': 2, 'Sell': 3, 'Strong Sell': 3}.get)
        df = df.dropna(subset=['Consensus'])
        return df
    
    def train(self, df):
        df = self.handleData(df)

        X_train, X_test, y_train, y_test = train_test_split(df.drop(columns=['Consensus']),
                                                            df['Consensus'],
                                                            test_size=0.2,
                                                            random_state=44)

        self.pipe.fit(X_train, y_train)
    def predict(self, df):
        df = super().cleanTest(df) # call parent class's cleanTest() method
        df['created_date'] = pd.to_datetime(df['created_date'], format='%Y-%m-%d').astype('int64') // 10**9
        df['Ticker'] = np.where(df['Ticker'].map(df['Ticker'].value_counts()) >= 10, df['Ticker'],df['Ticker'])#, 'Other'
#         df['Consensus'] = np.nan # set the target column to nan
#         X = self.pipe.transform(df)
        y_pred = self.pipe.predict(df)
        return y_pred
    

if __name__ == "__main__":
    model = ModelPipeline()
    model.train(df)

