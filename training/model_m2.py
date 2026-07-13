import torch, torch.nn as nn

class ResBlock(nn.Module):
    def __init__(self, c_in, c_out, stride=1):
        super().__init__()
        self.c1 = nn.Conv2d(c_in, c_out, 3, stride, 1, bias=False)
        self.b1 = nn.BatchNorm2d(c_out)
        self.c2 = nn.Conv2d(c_out, c_out, 3, 1, 1, bias=False)
        self.b2 = nn.BatchNorm2d(c_out)
        self.sc = (nn.Sequential() if (stride==1 and c_in==c_out)
                   else nn.Sequential(nn.Conv2d(c_in,c_out,1,stride,bias=False),
                                      nn.BatchNorm2d(c_out)))
        self.act = nn.ReLU(inplace=True)
    def forward(self,x):
        y = self.act(self.b1(self.c1(x)))
        y = self.b2(self.c2(y))
        return self.act(y + self.sc(x))

class ThetaEScaleNet(nn.Module):
    """Predict theta_E in ARCSEC from image + scalar pixel-scale."""
    def __init__(self, in_ch=1, widths=(32,64,128,256)):
        super().__init__()
        self.stem = nn.Sequential(nn.Conv2d(in_ch,widths[0],7,2,3,bias=False),
                                  nn.BatchNorm2d(widths[0]), nn.ReLU(inplace=True))
        self.layers = nn.Sequential(
            ResBlock(widths[0],widths[0]),
            ResBlock(widths[0],widths[1],2),
            ResBlock(widths[1],widths[2],2),
            ResBlock(widths[2],widths[3],2))
        self.gap = nn.AdaptiveAvgPool2d(1)
        feat = widths[3]
        self.head = nn.Sequential(nn.Linear(feat+1,128), nn.ReLU(inplace=True),
                                  nn.Linear(128,1))      # +1 = the scalar scale
    def forward(self, image, scale):                     # scale: [B,1] normalized
        f = self.gap(self.layers(self.stem(image)))      # [B,feat,1,1]
        f = torch.flatten(f,1)                            # [B,feat]
        return self.head(torch.cat([f,scale],dim=1)).squeeze(1)
