# Machine Learning Fundamentals

## What is Machine Learning?

Machine Learning (ML) is a subset of Artificial Intelligence that enables computers to learn from data without being explicitly programmed. Instead of writing rules manually, ML algorithms discover patterns in data and use them to make predictions or decisions.

## Types of Machine Learning

### 1. Supervised Learning
In supervised learning, the algorithm learns from labeled training data. Each training example includes an input and the correct output (label).

**Examples:**
- Classification: Spam detection, image recognition
- Regression: House price prediction, stock forecasting

**Common Algorithms:**
- Linear Regression
- Logistic Regression
- Decision Trees
- Random Forests
- Support Vector Machines (SVM)
- Neural Networks

### 2. Unsupervised Learning
The algorithm finds patterns in unlabeled data without predefined outputs.

**Examples:**
- Clustering: Customer segmentation
- Dimensionality Reduction: PCA, t-SNE
- Anomaly Detection: Fraud detection

**Common Algorithms:**
- K-Means Clustering
- Hierarchical Clustering
- Principal Component Analysis (PCA)
- Autoencoders

### 3. Reinforcement Learning
An agent learns by interacting with an environment, receiving rewards or penalties for actions.

**Examples:**
- Game playing (AlphaGo)
- Robotics
- Autonomous vehicles

## Neural Networks

### What is a Neural Network?
A neural network is a computational model inspired by biological neurons. It consists of layers of interconnected nodes (neurons) that process information.

### Components:
1. **Input Layer**: Receives the input features
2. **Hidden Layers**: Process information through weighted connections
3. **Output Layer**: Produces the final prediction
4. **Activation Functions**: Introduce non-linearity (ReLU, Sigmoid, Tanh)

### Backpropagation
Backpropagation is the algorithm used to train neural networks. It:
1. Performs a forward pass to compute predictions
2. Calculates the loss (error) between predictions and actual values
3. Propagates the error backward through the network
4. Updates weights using gradient descent to minimize the loss

## Deep Learning

Deep Learning uses neural networks with many hidden layers (deep networks) to learn hierarchical representations of data.

### Popular Architectures:
- **CNNs (Convolutional Neural Networks)**: Image processing
- **RNNs (Recurrent Neural Networks)**: Sequential data
- **Transformers**: Natural language processing
- **GANs (Generative Adversarial Networks)**: Data generation

## Model Evaluation

### Metrics for Classification:
- **Accuracy**: Correct predictions / Total predictions
- **Precision**: True Positives / (True Positives + False Positives)
- **Recall**: True Positives / (True Positives + False Negatives)
- **F1 Score**: Harmonic mean of Precision and Recall

### Metrics for Regression:
- **MSE (Mean Squared Error)**
- **RMSE (Root Mean Squared Error)**
- **MAE (Mean Absolute Error)**
- **R² Score**

## Overfitting and Underfitting

### Overfitting
The model learns the training data too well, including noise, and performs poorly on new data.

**Solutions:**
- More training data
- Regularization (L1, L2)
- Dropout
- Early stopping
- Cross-validation

### Underfitting
The model is too simple to capture the underlying patterns.

**Solutions:**
- More complex model
- More features
- Less regularization
- Train longer

## Best Practices

1. **Data Preprocessing**: Clean, normalize, and transform data
2. **Feature Engineering**: Create meaningful features
3. **Train/Validation/Test Split**: Properly evaluate model performance
4. **Hyperparameter Tuning**: Optimize model parameters
5. **Cross-Validation**: Robust performance estimation
6. **Ensemble Methods**: Combine multiple models for better results

## Feature Engineering

### What is Feature Engineering?
Feature engineering is the process of using domain knowledge to create new input features that make machine learning algorithms work better.

### Common Techniques

#### 1. Handling Missing Values
- **Deletion**: Remove rows/columns with missing data
- **Imputation**: Fill with mean, median, mode, or predicted values
- **Indicator Variables**: Create binary flags for missingness

#### 2. Encoding Categorical Variables
- **One-Hot Encoding**: Create binary columns for each category
- **Label Encoding**: Assign integer values to categories
- **Target Encoding**: Replace categories with target mean
- **Ordinal Encoding**: For ordered categories

#### 3. Feature Scaling
- **Standardization (Z-score)**: Mean=0, Std=1
- **Min-Max Normalization**: Scale to [0, 1]
- **Robust Scaling**: Uses median and IQR (handles outliers)

#### 4. Feature Transformation
- **Log Transform**: For skewed distributions
- **Box-Cox Transform**: Generalized power transformation
- **Polynomial Features**: Create interaction terms

#### 5. Feature Selection
- **Filter Methods**: Correlation, chi-square, mutual information
- **Wrapper Methods**: Forward/backward selection, RFE
- **Embedded Methods**: L1 regularization, tree importance

## Gradient Descent

### What is Gradient Descent?
Gradient descent is an optimization algorithm used to minimize the loss function by iteratively moving toward the steepest descent.

### Types of Gradient Descent

#### 1. Batch Gradient Descent
- Uses entire dataset for each update
- Stable but slow for large datasets
- Guaranteed convergence for convex functions

#### 2. Stochastic Gradient Descent (SGD)
- Uses single sample for each update
- Faster but noisy updates
- Can escape local minima

#### 3. Mini-Batch Gradient Descent
- Uses small batches (32, 64, 128 samples)
- Balance between batch and stochastic
- Most commonly used in practice

### Learning Rate
The learning rate controls the step size:
- **Too high**: May overshoot minimum, diverge
- **Too low**: Very slow convergence
- **Adaptive**: Adam, RMSprop, AdaGrad adjust automatically

### Momentum
Momentum accelerates gradient descent by accumulating velocity:
- Helps escape local minima
- Smooths out oscillations
- Common value: 0.9

## Cross-Validation

### Why Cross-Validation?
Cross-validation provides a more robust estimate of model performance than a single train-test split.

### Types of Cross-Validation

#### 1. K-Fold Cross-Validation
- Split data into K equal folds
- Train on K-1 folds, validate on 1 fold
- Repeat K times, average results
- Common K values: 5, 10

#### 2. Stratified K-Fold
- Maintains class distribution in each fold
- Essential for imbalanced datasets

#### 3. Leave-One-Out (LOO)
- K equals number of samples
- Most thorough but computationally expensive

#### 4. Time Series Split
- Respects temporal order
- Train on past, validate on future

## Ensemble Methods

### What are Ensemble Methods?
Ensemble methods combine multiple models to produce better predictions than any single model.

### Types of Ensembles

#### 1. Bagging (Bootstrap Aggregating)
- Train models on random subsets of data
- Average predictions (regression) or vote (classification)
- **Random Forest**: Bagging with decision trees

#### 2. Boosting
- Train models sequentially, focusing on errors
- Each model corrects previous mistakes
- **AdaBoost**: Adjusts sample weights
- **Gradient Boosting**: Fits residuals
- **XGBoost**: Optimized gradient boosting
- **LightGBM**: Fast gradient boosting
- **CatBoost**: Handles categorical features

#### 3. Stacking
- Train diverse base models
- Use meta-model to combine predictions
- Can capture complex relationships

## Bias-Variance Tradeoff

### Understanding the Tradeoff
- **Bias**: Error from overly simplistic assumptions (underfitting)
- **Variance**: Error from sensitivity to training data (overfitting)
- **Total Error** = Bias² + Variance + Irreducible Error

### Balancing Bias and Variance
- Simple models: High bias, low variance
- Complex models: Low bias, high variance
- Goal: Find the sweet spot that minimizes total error

## Regularization

### What is Regularization?
Regularization adds a penalty term to the loss function to prevent overfitting.

### Types of Regularization

#### L1 Regularization (Lasso)
- Adds sum of absolute weights to loss
- Produces sparse models (feature selection)
- Loss = Original Loss + λ * Σ|w|

#### L2 Regularization (Ridge)
- Adds sum of squared weights to loss
- Shrinks weights toward zero
- Loss = Original Loss + λ * Σw²

#### Elastic Net
- Combines L1 and L2 regularization
- Loss = Original Loss + λ₁ * Σ|w| + λ₂ * Σw²

## Dimensionality Reduction

### Why Reduce Dimensions?
- Reduce computational cost
- Remove noise and redundant features
- Enable visualization
- Mitigate curse of dimensionality

### Techniques

#### Principal Component Analysis (PCA)
- Linear transformation to orthogonal components
- Maximizes variance captured
- Unsupervised method

#### t-SNE (t-Distributed Stochastic Neighbor Embedding)
- Non-linear dimensionality reduction
- Excellent for visualization
- Preserves local structure

#### UMAP (Uniform Manifold Approximation)
- Faster than t-SNE
- Preserves global structure better
- Good for clustering visualization

## Handling Imbalanced Data

### The Problem
When classes are imbalanced, models tend to predict the majority class.

### Solutions

#### 1. Resampling
- **Oversampling**: Duplicate minority class (SMOTE)
- **Undersampling**: Remove majority class samples
- **Combination**: SMOTEENN, SMOTETomek

#### 2. Class Weights
- Assign higher weights to minority class
- Most algorithms support this parameter

#### 3. Threshold Adjustment
- Adjust decision threshold based on business needs
- Use precision-recall curve to find optimal threshold

#### 4. Anomaly Detection Approach
- Treat minority class as anomalies
- Use one-class SVM, isolation forest

## Hyperparameter Tuning

### What are Hyperparameters?
Hyperparameters are settings that control the learning process, not learned from data.

### Tuning Methods

#### 1. Grid Search
- Exhaustively search all combinations
- Guaranteed to find best in grid
- Computationally expensive

#### 2. Random Search
- Randomly sample hyperparameter space
- Often more efficient than grid search
- Better for high-dimensional spaces

#### 3. Bayesian Optimization
- Uses probabilistic model to guide search
- More efficient for expensive evaluations
- Libraries: Optuna, Hyperopt

#### 4. Automated ML (AutoML)
- Automates entire ML pipeline
- Tools: Auto-sklearn, H2O, Google AutoML

## Model Interpretability

### Why Interpretability Matters
- Build trust in predictions
- Debug and improve models
- Meet regulatory requirements
- Gain domain insights

### Interpretation Techniques

#### 1. Feature Importance
- Tree-based: Gini importance, permutation importance
- Linear models: Coefficient magnitudes

#### 2. SHAP (SHapley Additive exPlanations)
- Game-theoretic approach
- Consistent and locally accurate
- Works with any model

#### 3. LIME (Local Interpretable Model-agnostic Explanations)
- Explains individual predictions
- Creates local linear approximations

#### 4. Partial Dependence Plots
- Shows marginal effect of features
- Visualizes feature-target relationship

## ML Pipeline Best Practices

### 1. Data Pipeline
- Version control your data
- Automate data validation
- Document data transformations

### 2. Experiment Tracking
- Log hyperparameters and metrics
- Track model versions
- Tools: MLflow, Weights & Biases, Neptune

### 3. Model Deployment
- Containerize models (Docker)
- Set up CI/CD pipelines
- Monitor model performance in production

### 4. Model Monitoring
- Track prediction drift
- Monitor data quality
- Set up alerts for anomalies
