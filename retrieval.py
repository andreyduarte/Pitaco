import sqlite3
from database import get_db
import json
import numpy as np

def get_all_notifications():
    """
    Retrieves all notifications and their embeddings from the database.
    """
    db = get_db()
    cursor = db.execute('SELECT id, content, embedding FROM notifications')
    notifications = []
    for row in cursor.fetchall():
        notification_id, content, embedding_json = row
        embedding = json.loads(embedding_json)
        notifications.append({
            'id': notification_id,
            'content': content,
            'embedding': np.array(embedding)
        })
    return notifications

def cosine_similarity(embedding1, embedding2):
    """
    Calculates the cosine similarity between two embeddings.
    """
    dot_product = np.dot(embedding1, embedding2)
    norm_a = np.linalg.norm(embedding1)
    norm_b = np.linalg.norm(embedding2)
    return dot_product / (norm_a * norm_b)

def retrieve_relevant_notifications(query_embedding, threshold=0.8):
    """
    Retrieves notifications from the database that are relevant to the query embedding
    based on cosine similarity.
    """
    all_notifications = get_all_notifications()
    relevant_notifications = []
    for notification in all_notifications:
        similarity = cosine_similarity(query_embedding, notification['embedding'])
        if similarity >= threshold:
            relevant_notifications.append({
                'id': notification['id'],
                'content': notification['content'],
                'similarity': similarity
            })
    # Sort by similarity in descending order
    relevant_notifications.sort(key=lambda x: x['similarity'], reverse=True)
    return relevant_notifications

if __name__ == '__main__':
    # Example usage (assuming you have a way to generate a query embedding)
    # from llm_inference import _make_embedding_call
    # query_string = "This is a test query"
    # query_embedding = _make_embedding_call(query_string)
    # if query_embedding:
    #     relevant = retrieve_relevant_notifications(np.array(query_embedding))
    #     print("Relevant Notifications:")
    #     for r in relevant:
    #         print(f"ID: {r['id']}, Content: {r['content']}, Similarity: {r['similarity']:.4f}")
    # else:
    #     print("Failed to generate query embedding.")
    pass
