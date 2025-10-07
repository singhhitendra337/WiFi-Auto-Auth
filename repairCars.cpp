class Solution {
public:


    #define ll long long int

    bool check(vector<int>&nums,ll req,ll time)
    {
        int n=nums.size();


        for(int i=0;i<n;i++)
        {
            ll c=sqrt(time/nums[i]);

            req-=c;
            if(req<=0) return 1;
        }
        return req<=0;
    }


    long long repairCars(vector<int>& ranks, int cars) {

        ll s=0,e=1e15;

        ll ans;

        while(s<=e)
        {
            ll mid=(s+e)/2;

            bool poss=check(ranks,cars,mid);

            if(poss)
            {
                ans=mid;
                e=mid-1;
            }
            else s=mid+1;
        }
        return ans;

        


        
    }
};
