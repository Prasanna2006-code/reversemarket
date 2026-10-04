from sklearn.neural_network import MLPRegressor


def create_model(input_features):
    model = MLPRegressor(
        hidden_layer_sizes=(32, 16, 8),
        activation="relu",
        solver="adam",
        learning_rate_init=0.001,
        max_iter=2000,
        random_state=42
    )

    return model