# Code42 Splunk App
## Usage Examples

To query data imported through the Code42 Splunk app, you'll use Splunk's
built-in *Search & Reporting* app. The queries below should help you get started
with some of the data imported to the `code42` index.

### User Events

User events are imported to the `code42` index with a `c42userevent`
source type.

---

List which users are admins, and which are non-admins. Works best as a
Pie Chart visualization.

```
index="code42" sourcetype=c42userevent | search | eval role=if(searchmatch("roles{}.permissions{}.permission=admin"), "Admin", "User") | top limit=2 role
```
