# from imports import *
# seed = 1
#
# def load(datafile,inputsize):
#     # load dataset
#     dataframe = pandas.read_csv(datafile, delim_whitespace=True, header=None)
#     dataset = dataframe.values
#     # split into input (X) and output (Y) variables
#     X = dataset[:,0:inputsize]
#     Y = dataset[:,inputsize]
#     return (X,Y)
#
# # define  model
# def model():
#     global inputsize,netsize
#     # create model
#     model = Sequential()
#     model.add(Dense(netsize, input_dim=inputsize, kernel_initializer='normal', activation='relu'))
#     model.add(Dense(1, kernel_initializer='normal'))
#     # Compile model
#     model.compile(loss='mean_squared_error', optimizer='adam')
#     return model
#
# def make_pipeline():
#     # Define folding
#     kfold = KFold(n_splits=10)
#     estimators = []
#     estimators.append(('standardize', StandardScaler()))
#     estimators.append(('mlp', KerasRegressor(build_fn=model, epochs=500, batch_size=5, verbose=0)))
#     pipeline = Pipeline(estimators)
#     return pipeline
#
# def save_pipeline(p,w,s):
#     p.named_steps['mlp'].model.save_weights(w)
#     p.named_steps['mlp'].model=None
#     with open(s,"wb") as f:
#         pickle.dump(p,f)
#     p.named_steps['mlp'].model.load_weights(w)
#
# def load_pipeline(w,s):
#     p = make_pipeline()
#     with open(s,"rb") as f:
#         p=pickle.load(f)
#     p.named_steps['mlp'].model=model()
#     p.named_steps['mlp'].model.load_weights(w)
#     return p
#
#
#
