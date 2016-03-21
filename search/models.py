from __future__ import unicode_literals

from django.db import models

# Create your models here.
from django.db import models
from core.corelibs import *
import datetime,time
#from taggit.managers import TaggableManager
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save
# Create your models here.



class CYCategory(models.Model):
    card_type = models.CharField(max_length=1, choices=CARD_TYPES)
    category = models.CharField(max_length=255)
    cat_index = models.PositiveSmallIntegerField(default=100)
    is_active = models.BooleanField(default=True)

    def __unicode__(self):
        return self.category

    class Meta:
        verbose_name = 'Cyware News Category'
        verbose_name_plural = 'Cyware News Categories'


class CYStory(models.Model):
    curator = models.ForeignKey(settings.AUTH_USER_MODEL,null=True, blank=True,related_name='curator')
    card_type = models.CharField(max_length=1,choices=CARD_TYPES,default='P',verbose_name='card view')
    category = models.ForeignKey(CYCategory)
    story_type = models.CharField(max_length=1, choices=STORY_TYPES,default='S')
    sp_news_link = models.URLField(unique=True)
    card_score = models.IntegerField(choices= CARD_SCORE_CHOICES, default=1)
    card_shortID = models.CharField(max_length=8,unique=True)
    timestamp = models.DateTimeField(default=datetime.datetime.now)
    l_status = models.CharField(max_length=1,choices=CARD_STATUS,default='C')
    comments = models.CharField(max_length=500, null=True, blank=True)
    push_req = models.BooleanField(default=False)
    social_share_req = models.BooleanField(default=False)
    priority_q = models.CharField(max_length=1,choices=QUEUE_CHOICES,blank=True,null=True)

    def __unicode__(self):
        return self.sp_news_link

    def get_card_id(self):
        return self.card_shortID

    def get_time(self):
        return time.mktime(self.timestamp.timetuple())

    def get_ptime(self):
        return time.mktime(self.publish_time.timetuple())

    def get_curator(self):
        return self.curator.handle

    def get_sp_link(self):
        return self.sp_news_link

    def get_category(self):
        return self.category.category

    def get_created_time(self):
        return self.timestamp.time()

    class Meta:
        verbose_name = 'Cyware Story Lead'
        verbose_name_plural = 'Cyware Story Leads'


class CYStoryDetail(models.Model):

    story = models.OneToOneField(CYStory, related_name='story')
    title = models.CharField(max_length=70, db_index=True)
    text  = models.CharField(max_length=400, db_index=True)
    image = models.ImageField(max_length=255,blank=True, null=True)
    image_name = models.CharField(max_length=255,blank=True,null=True, verbose_name="image hint")
    sp_link_display = models.CharField(max_length=40,verbose_name='More at',null=True,blank=True)
    publish_time = models.DateTimeField(null=True,blank=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,related_name='creator')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,blank=True,related_name='reviewer')
    status = models.CharField(max_length=1, choices=STORY_STATUS,default='D')
    image_keywords = models.CharField(max_length=400,blank=True,null=True)

    def get_sp_display(self):
        return  self.sp_link_display

    def __unicode__(self):
        return self.story.card_shortID

    def get_card_type(self):
        return self.story.card_type
    get_card_type.admin_order_field = 'story__card_type'
    get_card_type.short_description = "Card Type"

    def get_card_type_desc(self):
        type_dict = dict(CARD_TYPES)
        return type_dict[self.story.card_type]
    get_card_type_desc.admin_order_field = 'story__card_type'
    get_card_type_desc.short_description = "Card Type"


    def get_card_score(self):
        return self.story.card_score
    get_card_score.short_description = "Card Score"

    def get_image(self):
        if self.image:
            return "https://"+ settings.AWS_STORAGE_BUCKET_NAME + ".s3.amazonaws.com/" + self.image.name
        else:
            return ""

    def get_card_id(self):
        return self.story.get_card_id()

    def get_time(self):
        return self.story.get_time()

    def get_ptime(self):
        return time.mktime(self.publish_time.timetuple())

    def get_curator(self):
        return self.story.get_curator()

    def get_sp_link(self):
        return self.story.get_sp_link()

    def get_category(self):
        return self.story.get_category()
    get_category.short_description = "Card Category"

    def get_created_time(self):
        return self.story.get_created_time()

    def get_readable_sp_link(self):
        return  "http://www.readability.com/m?url=" + self.get_sp_link()

    class Meta:
        verbose_name = 'Cyware Story Detail'
        verbose_name_plural = 'Cyware Story Details'
        permissions = (("can_publish", "Can publish stories"),('can_create',"card create details"))


class CYQueue(models.Model):

    name = models.CharField(max_length=50, unique=True)
    start_time = models.TimeField(db_index=True,blank=True,null=True)
    end_time = models.TimeField(db_index=True,blank=True,null=True)
    size = models.PositiveIntegerField(blank=True, null=True)
    assigned_creator = models.ManyToManyField(settings.AUTH_USER_MODEL,null=True, blank=True)
    story_list = models.ManyToManyField(CYStoryDetail,blank=True)

    def __unicode__(self):
        return self.name

    def current_size(self):
        return self.story_list.count()

@receiver(post_save, sender=CYStory)
def create_story_detail(sender, **kwargs):
    s = kwargs["instance"]
    c,_ =CYStoryDetail.objects.get_or_create(story=s)
    if s.priority_q:
        if s.priority_q =="A":
            q,_ = CYQueue.objects.get_or_create(name="ADHOC")
            q.story_list.add(c)
        else:
            q,_ = CYQueue.objects.get_or_create(name="WEEKEND")
            q.story_list.add(c)
    else:
        ql = CYQueue.objects.filter(start_time__lte=s.get_created_time(), end_time__gt=s.get_created_time())
        if ql.count():
            q = ql[0]
            if q.size > q.story_list.count():
                q.story_list.add(c)
            else:
                q,_ = CYQueue.objects.get_or_create(name="WEEKEND")
                q.story_list.add(c)
        else:
            q,_ = CYQueue.objects.get_or_create(name="WEEKEND")
            q.story_list.add(c)