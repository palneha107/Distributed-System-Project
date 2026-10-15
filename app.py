
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Three processes: P0, P1, P2
N = 3

clocks = {f"P{i}": [0, 0, 0] for i in range(N)}
logs = {f"P{i}": [] for i in range(N)}
messages = []


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/state")
def state():
    return jsonify({
        "clocks": clocks,
        "logs": logs,
        "buffer": messages
    })


@app.route("/api/event/local", methods=["POST"])
def local_event():
    process = request.json["process"]
    i = int(process[1])

    clocks[process][i] += 1
    logs[process].append("Local event occurred")

    return jsonify({"status": "ok"})


@app.route("/api/event/send", methods=["POST"])
def send():
    data = request.json
    sender = data["sender"]
    receiver = data["receiver"]
    i = int(sender[1])

    clocks[sender][i] += 1

    msg = {
        "id": len(messages) + 1,
        "sender": sender,
        "receiver": receiver,
        "text": data.get("text", "Msg"),
        "vector_clock": clocks[sender].copy()
    }

    messages.append(msg)
    logs[sender].append(f"Sent message to {receiver}")

    return jsonify({"status": "ok"})


@app.route("/api/event/deliver", methods=["POST"])
def deliver():
    msg_id = request.json["msg_id"]

    msg = next((m for m in messages if m["id"] == msg_id), None)

    if msg is None:
        return jsonify({"error": "Message not found"}), 404

    receiver = msg["receiver"]
    sender = msg["sender"]

    r = int(receiver[1])
    s = int(sender[1])

    clock = clocks[receiver]
    msg_clock = msg["vector_clock"]

    # Check causal ordering
    if msg_clock[s] != clock[s] + 1 or any(
        msg_clock[k] > clock[k]
        for k in range(N) if k != s
    ):
        return jsonify({"status": "blocked"}), 400

    # Update receiver's vector clock
    for k in range(N):
        clock[k] = max(clock[k], msg_clock[k])

    clock[r] += 1

    messages.remove(msg)
    logs[receiver].append(f"Received message from {sender}")

    return jsonify({"status": "ok"})


@app.route("/api/reset", methods=["POST"])
def reset():
    global clocks, logs, messages

    clocks = {f"P{i}": [0, 0, 0] for i in range(N)}
    logs = {f"P{i}": [] for i in range(N)}
    messages = []

    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
