# Deep Learning Fundamentals

## What is Deep Learning?

Deep Learning (DL) is a subset of Machine Learning that uses artificial neural networks with multiple layers (deep neural networks) to learn hierarchical representations of data. It excels at automatically discovering intricate patterns in large datasets.

## Neural Network Basics

### Neurons and Layers
- **Input Layer**: Receives raw data
- **Hidden Layers**: Process and transform data (multiple layers = "deep")
- **Output Layer**: Produces final predictions

### Activation Functions
Activation functions introduce non-linearity, enabling networks to learn complex patterns.

**Common Activation Functions:**
- **ReLU (Rectified Linear Unit)**: f(x) = max(0, x) - Most popular for hidden layers
- **Sigmoid**: f(x) = 1/(1 + e^(-x)) - Output range [0, 1]
- **Tanh**: f(x) = (e^x - e^(-x))/(e^x + e^(-x)) - Output range [-1, 1]
- **Softmax**: Converts outputs to probabilities (for multi-class classification)

## Deep Learning Architectures

### 1. Convolutional Neural Networks (CNNs)
Specialized for processing grid-like data (images, videos).

**Key Components:**
- **Convolutional Layers**: Extract local features using filters/kernels
- **Pooling Layers**: Reduce spatial dimensions (Max Pooling, Average Pooling)
- **Fully Connected Layers**: Final classification/regression

**Applications:**
- Image classification
- Object detection
- Face recognition
- Medical image analysis

### 2. Recurrent Neural Networks (RNNs)
Designed for sequential data with temporal dependencies.

**Variants:**
- **LSTM (Long Short-Term Memory)**: Handles long-term dependencies
- **GRU (Gated Recurrent Unit)**: Simplified LSTM with fewer parameters

**Applications:**
- Natural language processing
- Speech recognition
- Time series prediction
- Machine translation

### 3. Transformers
Attention-based architecture that processes sequences in parallel.

**Key Concepts:**
- **Self-Attention**: Weighs importance of different parts of input
- **Multi-Head Attention**: Multiple attention mechanisms in parallel
- **Positional Encoding**: Adds position information to embeddings

**Popular Models:**
- BERT (Bidirectional Encoder Representations)
- GPT (Generative Pre-trained Transformer)
- T5 (Text-to-Text Transfer Transformer)

### 4. Generative Adversarial Networks (GANs)
Two networks competing: Generator creates fake data, Discriminator detects fakes.

**Applications:**
- Image generation
- Style transfer
- Data augmentation
- Super-resolution

## Training Deep Networks

### Backpropagation
Algorithm for computing gradients by propagating errors backward through the network.

**Steps:**
1. Forward pass: Compute predictions
2. Calculate loss
3. Backward pass: Compute gradients
4. Update weights using optimizer

### Optimization Algorithms
- **SGD (Stochastic Gradient Descent)**: Basic optimizer
- **Adam**: Adaptive learning rates with momentum
- **RMSprop**: Adapts learning rate per parameter
- **AdaGrad**: Accumulates squared gradients

### Regularization Techniques
Prevent overfitting in deep networks:

- **Dropout**: Randomly disable neurons during training
- **Batch Normalization**: Normalize layer inputs
- **L1/L2 Regularization**: Penalize large weights
- **Data Augmentation**: Artificially expand training data
- **Early Stopping**: Stop training when validation loss increases

## Practical Considerations

### GPU Computing
Deep learning requires significant computational power:
- **CUDA**: NVIDIA's parallel computing platform
- **cuDNN**: Optimized deep learning primitives
- **TPUs**: Google's Tensor Processing Units

### Frameworks
Popular deep learning frameworks:
- **PyTorch**: Dynamic computation graphs, research-friendly
- **TensorFlow/Keras**: Production-ready, extensive ecosystem
- **JAX**: High-performance numerical computing

### Transfer Learning
Leverage pre-trained models for new tasks:
1. Start with a model trained on large dataset
2. Freeze early layers (general features)
3. Fine-tune later layers for specific task

## Common Challenges

### Vanishing/Exploding Gradients
- Use ReLU activation
- Apply batch normalization
- Use residual connections (skip connections)

### Overfitting
- Increase training data
- Apply regularization
- Use simpler architecture
- Early stopping

### Computational Cost
- Use mixed precision training
- Gradient checkpointing
- Model pruning and quantization

## Advanced Architectures

### ResNet (Residual Networks)
ResNet introduced skip connections that allow gradients to flow directly through the network.

**Key Concepts:**
- **Residual Blocks**: Learn residual functions F(x) + x
- **Skip Connections**: Identity mappings bypass layers
- **Deep Networks**: Enables training of 100+ layer networks
- **Variants**: ResNet-18, ResNet-50, ResNet-101, ResNet-152

### Inception Networks
Inception uses multiple filter sizes in parallel within each layer.

**Features:**
- **Multi-scale Processing**: 1x1, 3x3, 5x5 convolutions in parallel
- **Dimensionality Reduction**: 1x1 convolutions reduce computation
- **Auxiliary Classifiers**: Help gradient flow during training

### EfficientNet
EfficientNet systematically scales network depth, width, and resolution.

**Compound Scaling:**
- **Depth**: Number of layers
- **Width**: Number of channels
- **Resolution**: Input image size
- **Balanced Scaling**: Optimal ratio between dimensions

### Vision Transformers (ViT)
Applies transformer architecture to image classification.

**How it Works:**
1. Split image into fixed-size patches (e.g., 16x16)
2. Flatten patches and add positional embeddings
3. Process through transformer encoder
4. Use [CLS] token for classification

**Advantages:**
- Captures global context from the start
- Scales well with data and compute
- State-of-the-art on many benchmarks

## Natural Language Processing with Deep Learning

### Word Embeddings
Dense vector representations of words.

**Methods:**
- **Word2Vec**: Skip-gram and CBOW models
- **GloVe**: Global vectors from co-occurrence matrix
- **FastText**: Subword embeddings for rare words

### Sequence-to-Sequence Models
Encoder-decoder architecture for sequence transformation.

**Applications:**
- Machine translation
- Text summarization
- Question answering

**Components:**
- **Encoder**: Processes input sequence
- **Decoder**: Generates output sequence
- **Attention**: Focuses on relevant input parts

### BERT (Bidirectional Encoder Representations from Transformers)
Pre-trained language model using masked language modeling.

**Pre-training Tasks:**
- **Masked Language Model (MLM)**: Predict masked tokens
- **Next Sentence Prediction (NSP)**: Predict if sentences are consecutive

**Fine-tuning:**
- Add task-specific head
- Fine-tune on downstream task
- Works for classification, NER, QA, etc.

### GPT (Generative Pre-trained Transformer)
Autoregressive language model for text generation.

**Characteristics:**
- **Unidirectional**: Left-to-right attention
- **Generative**: Predicts next token
- **Few-shot Learning**: Learns from examples in prompt
- **Scaling Laws**: Performance improves with size

### Large Language Models (LLMs)
Massive transformer models trained on internet-scale data.

**Capabilities:**
- Text generation and completion
- Question answering
- Code generation
- Reasoning and analysis
- Multi-turn conversation

**Techniques:**
- **Instruction Tuning**: Train to follow instructions
- **RLHF**: Reinforcement Learning from Human Feedback
- **Chain-of-Thought**: Step-by-step reasoning

## Object Detection

### Two-Stage Detectors
First propose regions, then classify.

**R-CNN Family:**
- **R-CNN**: Selective search + CNN features
- **Fast R-CNN**: ROI pooling for efficiency
- **Faster R-CNN**: Region Proposal Network (RPN)
- **Mask R-CNN**: Adds instance segmentation

### One-Stage Detectors
Direct prediction without region proposals.

**Popular Models:**
- **YOLO (You Only Look Once)**: Real-time detection
- **SSD (Single Shot Detector)**: Multi-scale feature maps
- **RetinaNet**: Focal loss for class imbalance

### Key Concepts
- **Anchor Boxes**: Predefined bounding box shapes
- **Non-Maximum Suppression (NMS)**: Remove duplicate detections
- **IoU (Intersection over Union)**: Overlap metric
- **mAP (mean Average Precision)**: Evaluation metric

## Image Segmentation

### Semantic Segmentation
Classify each pixel into a category.

**Architectures:**
- **FCN (Fully Convolutional Networks)**: Replace FC layers with conv
- **U-Net**: Encoder-decoder with skip connections
- **DeepLab**: Atrous convolutions and CRF

### Instance Segmentation
Detect and segment individual object instances.

**Methods:**
- **Mask R-CNN**: Extends Faster R-CNN with mask branch
- **YOLACT**: Real-time instance segmentation

### Panoptic Segmentation
Combines semantic and instance segmentation.
- Assigns class to every pixel
- Distinguishes individual instances of "things"
- Treats "stuff" (sky, road) as single regions

## Generative Models

### Variational Autoencoders (VAEs)
Probabilistic generative model with latent space.

**Components:**
- **Encoder**: Maps input to latent distribution
- **Latent Space**: Continuous, regularized representation
- **Decoder**: Reconstructs from latent samples

**Loss Function:**
- Reconstruction loss + KL divergence

### Diffusion Models
Generate data by learning to reverse a noise process.

**Process:**
1. **Forward**: Gradually add noise to data
2. **Reverse**: Learn to denoise step by step
3. **Sampling**: Start from noise, iteratively denoise

**Popular Models:**
- Stable Diffusion
- DALL-E 2
- Midjourney

### Neural Style Transfer
Apply artistic style to content images.

**Method:**
- Extract content from one image
- Extract style from another image
- Optimize to match both

## Reinforcement Learning with Deep Learning

### Deep Q-Networks (DQN)
Combines Q-learning with deep neural networks.

**Key Innovations:**
- **Experience Replay**: Store and sample past experiences
- **Target Network**: Stabilize training with delayed updates
- **Applications**: Atari games, robotics

### Policy Gradient Methods
Directly optimize the policy.

**Algorithms:**
- **REINFORCE**: Monte Carlo policy gradient
- **Actor-Critic**: Combine value and policy learning
- **PPO (Proximal Policy Optimization)**: Stable policy updates
- **A3C**: Asynchronous advantage actor-critic

### Model-Based RL
Learn a model of the environment.

**Advantages:**
- Sample efficient
- Can plan ahead
- Transfer to new tasks

## Advanced Training Techniques

### Data Augmentation
Artificially expand training data.

**Image Augmentations:**
- Rotation, flipping, cropping
- Color jittering, brightness adjustment
- Cutout, Mixup, CutMix
- AutoAugment: Learned augmentation policies

### Learning Rate Schedules
Adjust learning rate during training.

**Strategies:**
- **Step Decay**: Reduce by factor at epochs
- **Cosine Annealing**: Smooth cosine decrease
- **Warmup**: Start low, increase gradually
- **One Cycle**: Increase then decrease

### Knowledge Distillation
Transfer knowledge from large to small model.

**Process:**
1. Train large "teacher" model
2. Train small "student" to match teacher outputs
3. Use soft labels (probabilities) for richer signal

### Self-Supervised Learning
Learn representations without labels.

**Methods:**
- **Contrastive Learning**: SimCLR, MoCo
- **Masked Prediction**: MAE, BEiT
- **Clustering**: SwAV, DINO

## Model Optimization for Deployment

### Quantization
Reduce precision of weights and activations.

**Types:**
- **Post-training Quantization**: Quantize after training
- **Quantization-Aware Training**: Train with quantization
- **INT8/INT4**: Common target precisions

### Pruning
Remove unnecessary weights or neurons.

**Approaches:**
- **Magnitude Pruning**: Remove small weights
- **Structured Pruning**: Remove entire filters/layers
- **Lottery Ticket Hypothesis**: Find sparse subnetworks

### Neural Architecture Search (NAS)
Automatically design network architectures.

**Methods:**
- **Reinforcement Learning**: Controller generates architectures
- **Evolutionary**: Mutate and select architectures
- **Differentiable**: Gradient-based search (DARTS)

## Ethical Considerations in Deep Learning

### Bias and Fairness
- Training data can encode societal biases
- Models may discriminate against groups
- Need diverse datasets and fairness metrics

### Environmental Impact
- Large models require significant energy
- Carbon footprint of training
- Need for efficient architectures

### Deepfakes and Misuse
- Generative models can create fake content
- Potential for misinformation
- Detection and watermarking research
