import torch
import os
from tqdm import tqdm

class Trainer:
    def __init__(self) -> None:
        self.model = None
        self.optimizer = None
        self.loss_fn = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.history = {
            "params" : {
                "lr": None,
                "epochs" : None,
                "is_val" : None,
                "model" : None,
            },
            "validation" : {
                "loss" : []
            },
            "train" : {
                "loss" :  []
            }
        }
    def set_loss(self, loss_fn):
        self.loss_fn = loss_fn
        return self

    def set_model(self, model, name):
        self.model = model
        self.model.to(self.device)
        self.history['params']['model'] = name
        print(f"[INFO] Model's device is : {self.device}")
        return self

    def set_optimizer(self, optimizer):
        self.optimizer = optimizer
        return self

    def save(self, model_path : str = "model.pth", history_path : str = "history.txt"):
        torch.save(self.model.state_dict(), model_path)
        torch.save(self.history, history_path)

    def get_history(self, history_path):
        assert os.path.exists(history_path), "[ERROR] history path does not exist"
        return torch.load(history_path)
    
    def get_model(self, model_path):
        assert os.path.exists(model_path), "[ERROR] path does not exist"
        return torch.load(model_path)
    
    def fit(self, train_data, validation_data=None, learning_rate=1e-4, epochs=1, verbose=True, sim_clr=False, use_context=False, weight_decay=1e-6):
        assert self.model is not None, "[ERROR] set or load the model first throught .set_model() or .load_model()"
        assert self.optimizer is not None, "[ERROR] set the optimizer first throught .set_optimizer()"
        assert self.loss_fn is not None, "[ERROR] set the loss function first throught .set_loss()"

        self.optimizer = self.optimizer(self.model.parameters(), lr=learning_rate, weight_decay=weight_decay)

        self.history["params"]["lr"] = learning_rate
        self.history["params"]["epochs"] = epochs
        self.history["params"]["is_val"] = True if validation_data is not None else False

        for epoch in tqdm(range(epochs)):
            train_loss, val_loss = None, None
            if sim_clr :
                train_loss = self._trainCLR(train_data, use_context)
                val_loss = self._validateCLR(validation_data, use_context)
            else:
                train_loss = self._train(train_data)
                val_loss = self._validate(validation_data)

            self._print_epoch(epoch, train_loss, val_loss, verbose)

            self.history['train']['loss'].append(train_loss)
            self.history['validation']['loss'].append(val_loss)

            
        return self.model


    def evaluate(self, test_data):
        pass

    def _train(self, train_data):
        # print("Training...")
        losses = []
        self.model.train()
        for batch_x, batch_y in train_data:  
            batch_x, batch_y = batch_x.to(self.device), batch_y.to(self.device)
            y_hat = self.model(batch_x)
            loss = self.loss_fn(y_hat, batch_y)
            losses.append(loss.item())
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
        return sum(losses)/len(train_data)
    
    def _validate(self, validation_data):
        # print("Validating...")
        losses = []
        self.model.eval()
        with torch.no_grad():
            for batch_x, batch_y in validation_data:
                batch_x, batch_y = batch_x.to(self.device), batch_y.to(self.device)
                y_hat = self.model(batch_x)
                loss = self.loss_fn(y_hat, batch_y)
                losses.append(loss.item())
        return sum(losses)/len(validation_data)
    

    def _trainCLR(self, train_data, use_context=False):
        # print("Training...")
        losses = []
        self.model.train()
        for data in train_data:
            output = None
            if use_context:
                batch_x, batch_y, context_x, context_y = data
                batch_x, batch_y = batch_x.to(self.device), batch_y.to(self.device)
                context_x, context_y = context_x.to(self.device), context_y.to(self.device)
                output = self.model(batch_x, batch_y, context_x, context_y)
            else:
                batch_x, batch_y = data
                batch_x, batch_y = batch_x.to(self.device), batch_y.to(self.device)
                output = self.model(batch_x, batch_y)

            Z1, Z2 = output["projection_head"]
            loss = self.loss_fn(Z1,Z2)
            losses.append(loss.item())
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

        return sum(losses)/len(train_data)

    def _validateCLR(self, validation_data, use_context=False):
        # print("Validating...")
        losses = []
        self.model.eval()
        with torch.no_grad():
            for data in validation_data:
                output = None
                if use_context:
                    batch_x, batch_y, context_x, context_y = data
                    batch_x, batch_y = batch_x.to(self.device), batch_y.to(self.device)
                    context_x, context_y = context_x.to(self.device), context_y.to(self.device)
                    output = self.model(batch_x, batch_y, context_x, context_y)
                else:
                    batch_x, batch_y = data
                    batch_x, batch_y = batch_x.to(self.device), batch_y.to(self.device)
                    output = self.model(batch_x, batch_y)
                
                Z1, Z2 = output["projection_head"]
                loss = self.loss_fn(Z1,Z2)
                losses.append(loss.item())

        return sum(losses)/len(validation_data)
    
    def _print_epoch(self, epoch, train_loss, val_loss, verbose):
        if epoch % 5 == 0 and verbose or epoch <1:
            print(f"Epoch : {epoch}, Train loss : {train_loss}, Validation loss : {val_loss}")

