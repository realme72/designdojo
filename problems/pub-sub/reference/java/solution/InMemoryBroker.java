package solution;

import contract.Broker;
import contract.DuplicateSubscription;
import contract.DuplicateTopic;
import contract.InvalidArgument;
import contract.Message;
import contract.UnknownGroup;
import contract.UnknownTopic;

import java.util.List;
import java.util.concurrent.ConcurrentHashMap;

final class InMemoryBroker implements Broker {
    private final ConcurrentHashMap<String, Topic> topics = new ConcurrentHashMap<>();

    private Topic topic(String name) {
        Topic t = topics.get(name);
        if (t == null) throw new UnknownTopic(name);
        return t;
    }

    private Subscription sub(String topic, String group) {
        Subscription s = topic(topic).subscriptions.get(group);
        if (s == null) throw new UnknownGroup(group);
        return s;
    }

    @Override
    public void createTopic(String name) {
        if (topics.putIfAbsent(name, new Topic()) != null) throw new DuplicateTopic(name);
    }

    @Override
    public long publish(String topic, String payload) {
        return topic(topic).append(payload);
    }

    @Override
    public void subscribe(String topic, String group, boolean fromBeginning) {
        Topic t = topic(topic);
        synchronized (t) {
            if (t.subscriptions.containsKey(group)) throw new DuplicateSubscription(group);
            t.subscriptions.put(group, new Subscription(t, fromBeginning ? 0 : t.end()));
        }
    }

    @Override
    public List<Message> poll(String topic, String group, int max) {
        if (max < 1) throw new InvalidArgument("max " + max);
        return sub(topic, group).poll(max);
    }

    @Override
    public long lag(String topic, String group) {
        return sub(topic, group).lag();
    }

    @Override
    public void seek(String topic, String group, long offset) {
        sub(topic, group).seek(offset);
    }
}
