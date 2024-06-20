from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from organization.models import MailRecipient
from api.serializers.mail import MailSerializer
from rest_framework import status

# api to get all the mails
class MailApiView(APIView):
    permission_classes = [IsAuthenticated]


    def get(self, request):
        mails = MailRecipient.objects.all().order_by('-id')
        serilizer = MailSerializer(mails, many=True)

        return Response(serilizer.data, status=status.HTTP_200_OK)

MailApiView=MailApiView.as_view()

# dicount creating api
class MailCreateApiView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data

        serializer = MailSerializer(data=data)
        try:
            if serializer.is_valid():
                serializer.save()

                return Response("Mail added", status=status.HTTP_200_OK)
            else:
                return Response("Mail already exists", 400)
        except Exception as e:
            return Response(f"Error in data", status=status.HTTP_400_BAD_REQUEST)

# mail updating Api   
class MailUpdateApiView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        mail_id = kwargs.get('pk')
        mail = MailRecipient.objects.get(pk=mail_id)

        data =request.data
        
        serializer = MailSerializer(mail, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response("Mail Updated", status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# mail deleting Api
class MailDeleteApiView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        mail_id = kwargs.get('pk')
        mail = MailRecipient.objects.get(pk=mail_id)
        try:
            # mail.is_deleted=True
            mail.status = False
            mail.save()
            return Response("Mail has been deleted", status=status.HTTP_200_OK)

        except Exception as e:
            return Response(e, status=status.HTTP_400_BAD_REQUEST)


