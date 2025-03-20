import torch
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import make_blobs
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

X, y=make_blobs(n_samples=1000, centers=10, random_state=42)

scaler=StandardScaler()
X=scaler.fit_transform(X)

X_train, X_test, y_train, y_test= train_test_split(X,y,test_size=0.2,random_state=42)

X_train_tensor =torch.tensor(X_train, dtype=torch.float32)
y_train_tensor =torch.tensor(y_train, dtype=torch.long)
X_test_tensor =torch.tensor(X_train, dtype=torch.float32)
y_test_tensor =torch.tensor(y_train, dtype=torch.long)

input_dim = X_train_tensor.shape[1]
hidden_dim = 16
output_dim = 10

W1 = torch.randn(input_dim, hidden_dim, dtype=torch.float32, requires_grad=True)
b1 = torch.zeros(hidden_dim, dtype=torch.float32,  requires_grad=True)
W2 = torch.randn(hidden_dim, output_dim, dtype=torch.float32, requires_grad=True)
b2 = torch.zeros(output_dim, dtype=torch.float32,  requires_grad=True)

def relu(x):
  return torch.maximum(x, torch.zeros_like(x))

def softmax(x):
  e_x = torch.exp(x-torch.max(x, dim=1, keepdim=True)[0])
  return e_x / torch.sum(e_x, dim=1, keepdim=True)

def forward(X):
  Z1=torch.matmul(X, W1) + b1
  A1=relu(Z1)

  Z2=torch.matmul(A1, W2) + b2
  A2=softmax(Z2)
  return A2

def cross_entropy_loss(y_pred, y_true):
 # num_samples = y_true.shape[0]
  y_one_hot = torch.zeros_like(y_pred)
  y_one_hot[torch.arange(len(y_true)), y_true] = 1
  return -torch.mean(torch.sum(y_one_hot * torch.log(y_pred), dim=1))

learning_rate=0.01
epochs=100

for epoch in range(epochs):
  y_pred = forward(X_train_tensor)
  loss = cross_entropy_loss(y_pred, y_train_tensor)

  loss.backward()
  with torch.no_grad():
    W1 -= learning_rate * W1.grad
    b1 -= learning_rate * b1.grad
    W2 -= learning_rate * W2.grad
    b2 -= learning_rate * b2.grad

    W1.grad.zero_()
    b1.grad.zero_()
    W2.grad.zero_()
    b2.grad.zero_()

  if (epoch+1) % 10 == 0:
    print(f'Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}')

def predict(X):
  with torch.no_grad():
    y_pred = forward(X)
    _, predicted = torch.max(y_pred, dim=1)
    return predicted

# y_pred_train = predict(X_train_tensor)
y_pred_test = predict(X_test_tensor)
accuracy = (y_pred_test == y_test_tensor).sum().item() / y_test_tensor.size(0)
print(f'Accuracy on test data: {accuracy * 100:.2f}%')

def plot_decision_boundary(X, y, model):
  x_min, x_max = X[:, 0].min() -1, X[:, 0].max() +1
  y_min, y_max = X[:, 1].min() -1, X[:, 1].max() +1
  xx, yy= torch.meshgrid(torch.linspace(x_min , x_max, 100), torch.linspace(y_min, y_max, 100))
  grid = torch.stack([xx.ravel(), yy.ravel()], dim=1)

  y_pred = predict(grid)
  predicted = y_pred.view(xx.shape)

  plt.contourf(xx, yy, predicted.numpy(), alpha=0.8)
  plt.scatter(X[:, 0], X[:, 1], c=y, edgecolors='k', marker='o', s=50)
  plt.show()

plot_decision_boundary(X_train_tensor, y_train_tensor, forward)